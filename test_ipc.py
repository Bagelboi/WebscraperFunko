from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys  # Added missing import
import subprocess
import time

class ProdutoPayload:
    def __init__(s, sku, imagens=[], specs=dict()):
        s.sku = sku
        s.imagens = imagens
        s.specs = specs
    def __str__(s):
        specs_s = ""
        for k,v in s.specs.items():
            specs_s += f"{v},"
        return ";".join([s.sku, ",".join(s.imagens), specs_s])

def mocaSearch(driver, nome, sku):
    nome_new = nome.replace(" ", "+")
    url = "https://www.mocadopop.com.br/buscar?q=" + nome_new
    driver.get(url)
    
    try:
        # 1. Wait for li with class listagem-linha and get the last one
        all_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.listagem-linha"))
        )
        first_item = all_items[-1]  # Get the last element
        
        # 2. Get the first child that is <a> and goto its href
        link = first_item.find_element(By.CSS_SELECTOR, "a.produto-sobrepor")
        product_url = link.get_attribute("href")
        driver.get(product_url)
        
        # 3. Wait for ul with class miniaturas
        thumbnails = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.miniaturas"))
        )
        
        # 4. Get all child of ul that are <a> with attribute data-imagem-grande and print its value
        image_links = thumbnails.find_elements(By.CSS_SELECTOR, "a[data-imagem-grande]")
        payload = ProdutoPayload(sku)
        for link in image_links:
            payload.imagens.append( link.get_attribute("data-imagem-grande") )
        return payload
            
    except Exception as e:
        print(f"An error occurred: {e}")
        
def eeSearch(driver, sku):
    sku = sku.upper()
    payload = ProdutoPayload(sku)
    try:
        # 1. Go to the search URL
        driver.get(f"https://www.entertainmentearth.com/s/?query1={sku}")
        
        # Wait for product results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-results"))
        )
        
        # 2. Find the product with matching SKU
        product_results = driver.find_element(By.CLASS_NAME, "product-results")
        products = product_results.find_elements(By.XPATH, "./div")
        
        found = False
        for product in products:
            try:
                item_number = product.find_element(By.CLASS_NAME, "item-number")
                if item_number.text == sku:
                    product.click()
                    found = True
                    # Wait for product page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "owl-inset-arrows"))
                    )
                    break
            except:
                continue
                
        if not found:
            print(f"Product with SKU {sku} not found")
            return None
            
        # 3. Click through all carousel items
        owl_inset = driver.find_elements(By.CLASS_NAME, "owl-inset-arrows")[1]
        carousel_items = owl_inset.find_elements(By.CLASS_NAME, "owl-item")
        
        for item in carousel_items:
            try:
                item.click()
                time.sleep(0.2)  # slight delay
            except:
                continue
                
        # 4. Get all image hrefs
        carousel_wrapper = driver.find_element(By.CSS_SELECTOR, ".product-images-carousel-wrapper")
        [payload.imagens.append(a.get_attribute("href")) for a in carousel_wrapper.find_elements(By.TAG_NAME, "a")]
        
        # 5. Get specifications data
        try:
            specs_div = driver.find_element(By.ID, "Specifications")
            list_items = specs_div.find_elements(By.TAG_NAME, "li")
            key_filter = ["Age:", "Company:"]
            for li in list_items:
                try:
                    spans = li.find_elements(By.CSS_SELECTOR, "span")
                    key = spans[0].text.strip()
                    if key not in key_filter:
                        payload.specs[key] = spans[1].text.strip()
                except:
                    continue
        except Exception as e:
            print(f"Could not retrieve specifications: {str(e)}")
        
        return payload
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None



def mercadoLivreLookup(driver, search_query, sku):
    # URL encode the search query
    url = f"https://lista.mercadolivre.com.br/{search_query}"
    payload = ProdutoPayload(sku)
    
    try:
        # Navigate to the search page
        driver.get(url)
        
        # Wait for and click first product (with more robust waiting)
        first_product = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.poly-component__title")))
        first_product.click()
    
        
        # Get all zoomable images
        zoom_images = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[data-zoom]")))
        
        for img in zoom_images:
            src = img.get_attribute("src")
            if src:
                payload.imagens.append(src)
                
    except Exception as e:
        print(f"An error occurred during Mercado Livre lookup: {str(e)}")
        # Consider re-raising or handling specific exceptions differently
    
    return payload

##def googleShoppingSearch(driver, query, sku):
#   Bem bunda, Google ofusca tudo
##    payload = ProdutoPayload(sku)
##    try:
##        # Navigate to Google Shopping
##        driver.get("https://www.google.com/shopping")
##        
##        # Wait for page to load completely
##        WebDriverWait(driver, 10).until(
##            EC.presence_of_element_located((By.NAME, "q"))
##        )
##        
##        # Find the search input field
##        search_box = driver.find_element(By.NAME, "q")
##        
##        # Clear any existing text and enter the query
##        search_box.clear()
##        search_box.send_keys(query)
##        
##        # Submit the search
##        search_box.send_keys(Keys.RETURN)
##        
##        # Wait for results to load
##        WebDriverWait(driver, 10).until(
##            EC.presence_of_element_located((By.CSS_SELECTOR, ".sh-sr__shop-result-group, .sh-dgr__grid-result"))
##        )
##        
##        # Find all shop result groups
##        result_groups = driver.find_elements(By.CSS_SELECTOR, ".sh-sr__shop-result-group")
##        
##        if len(result_groups) == 3:
##            # Scenario 1: 3 groups (best match + other results)
##            print("Found 3 result groups (best match + other results)")
##            # Wait for images in the best match section
##            WebDriverWait(driver, 10).until(
##                EC.presence_of_element_located((By.CSS_SELECTOR, ".sh-div__image"))
##            )
##            images = driver.find_elements(By.CSS_SELECTOR, ".sh-div__image")
##            
##            for img in images[:5]:
##                payload.imagens.append("Image src:", img.get_attribute("src"))
##                
##        elif len(result_groups) == 2:
##            # Scenario 2: 2 groups (just regular results)
##            print("Found 2 result groups (regular results)")
##            # Get the first 3 products
##            products = driver.find_elements(By.CSS_SELECTOR, ".sh-dgr__grid-result")[:3]
##            
##            for i, product in enumerate(products, 1):
##                try:
##                    print(f"\nProcessing product {i}")
##                    
##                    # Scroll to the element with JavaScript
##                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product)
##                    
##                    # Wait for the element to be clickable
##                    WebDriverWait(driver, 10).until(
##                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".sh-dgr__grid-result"))
##                    )
##                    
##                    # Click using JavaScript as a fallback
##                    try:
##                        product.click()
##                    except:
##                        driver.execute_script("arguments[0].click();", product)
##                    
##                    # Wait for image to load
##                    WebDriverWait(driver, 10).until(
##                        EC.presence_of_element_located((By.CSS_SELECTOR, ".sh-div__image"))
##                    )
##
##                    images = driver.find_elements(By.CSS_SELECTOR, ".sh-div__image")
##                    
##                    for img in images[:5]:
##                        payload.imagens.append("Image src:", img.get_attribute("src"))
##
##                except Exception as e:
##                    print(f"Error processing product {i}:", str(e))
##                    continue
##                    
##        else:
##            print(f"Unexpected number of result groups found: {len(result_groups)}")
##            return None
##        
##        return payload        
##            
##    except Exception as e:
##        print("Error in googleShoppingSearch:", str(e))

