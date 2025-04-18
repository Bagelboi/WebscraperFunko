from playwright.async_api import async_playwright
import test_ipc as popscraper
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class InfoPayload:
        def __init__(s, number, name, sku):
                s.sku = sku
                s.number = number
                s.name = name
        def __str__(s):
                ";".join([s.sku, s.name, s.number])

async def get_item_info(item_locator, sku):
        # Product number (might be missing)
        product_number = ""
        print(item_locator)
        product_number_selector = item_locator.locator('span[ng-bind="item.attributes.refNumber"]')
        if await product_number_selector.count() > 0:
            product_number = (await product_number_selector.first.inner_text()).strip()
        # Product name (should always exist)
        product_name = (await item_locator.locator('a.catalog-item-name').first.inner_text()).strip()

        # AKA information (might be missing)
        aka_selector = item_locator.locator('div[ng-if="item.attributes.aka"]')
        if await aka_selector.count() > 0:
            aka_text = (await aka_selector.first.inner_text()).strip()
            if aka_text.lower().find(product_name.lower()) > -1:  
                    product_name = f"{aka_text}"
            else:
                    product_name = f"{product_name} {aka_text}"

        return InfoPayload(product_number, product_name, sku)

async def get_all_items_info(page, sku):
        await page.locator('div.catalog-item-info').first.wait_for(
            state='attached', 
            timeout=5000
        )
        items_info = []
        catalog_items = page.locator('div.catalog-item-info')
        item_count = await catalog_items.count()
        
        print(f"Found {item_count} items to process")
        
        for i in range(item_count):
            try:
                item = catalog_items.nth(i)
                # Additional wait for each item to be stable
                await item.wait_for(state='visible', timeout=5000)
                item_info = await get_item_info(item, sku)
                items_info.append(item_info)
            except Exception as e:
                print(f"Error processing item {i}: {str(e)}")
        return items_info
    
async def hobby_db_lookup(page, sku, context):
    """Look up a product on HobbyDB by SKU."""
    url = "https://www.hobbydb.com/marketplaces/hobbydb/catalog_items?filters[q][0]="
    await page.goto(url + sku)
    info = {
            "main":None,
            }

    # Get main item info
    try:
            main_item = page.locator('div.catalog-item-info').first
            await main_item.wait_for(state='attached', timeout=5000)
            info["main"] = await get_item_info(main_item, sku)  # Add the original SKU to the result
            
            # Check for variants
            variant_selector = main_item.locator('span[ng-if=" item.attributes.variantsCount > 1"] > a')
            if await variant_selector.count() > 0:
                href = await variant_selector.first.get_attribute('href')
                new_page = await context.new_page()
                await new_page.goto("https://www.hobbydb.com" + href)
                #await new_page.wait_for_load_state('networkidle')
                info["variants"] = await get_all_items_info(new_page, sku)
                await new_page.close()

    except:
            print(f"Didn't find item with sku {sku}")
    return info    

async def process_sku(browser, sku):
    """Process a single SKU lookup."""
    context = await browser.new_context( )
    context.set_default_timeout(5000)
    page = await context.new_page()
    try:
        result = await hobby_db_lookup(page, sku, context)
        await context.close()
        return result
    except Exception as e:
        await context.close()
        print("Error happend during processing")
