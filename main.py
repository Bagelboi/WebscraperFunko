from playwright.async_api import async_playwright
import test_ipc as popscraper
import test_browser as hobbyscraper
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def createCsvEntry(searchtype, sku, payload):
    if payload is not None and sku is not None:
        return ";".join([sku, searchtype, str(payload)]) + "\n"
    return ""


async def main():
    skus = input("Enter SKUs separated by commas: ").strip().split(',')
    skus = [sku.strip() for sku in skus if sku.strip()]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Process SKUs with concurrency limit of 5
        semaphore = asyncio.Semaphore(5)
        
        async def limited_process(sku):
            async with semaphore:
                return await hobbyscraper.process_sku(browser, sku)
        
        tasks = [limited_process(sku) for sku in skus]
        results = await asyncio.gather(*tasks)
        await browser.close()

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Print results
        remove_parantese = str.maketrans({
                '(':'',
                ')':''})
        f = open("teste.csv", "w")
        for result in results:
            if result is not None and "main" in result:
                    main_res = result["main"]
                    main_res.name = main_res.name.translate(remove_parantese)
                    print(result)
                    if main_res is not None:
                            #f.write(createCsvEntry("Moça", main_res.sku, popscraper.mocaSearch(driver, " ".join([main_res.name, main_res.number]), main_res.sku)))
                            #f.write(createCsvEntry("EE", main_res.sku, popscraper.eeSearch(driver, main_res.sku)))
                            f.write(createCsvEntry("ML", main_res.sku, popscraper.mercadoLivreLookup(driver, " ".join(["funko", main_res.name, main_res.number]), main_res.sku)))
                    if "variants" in result:
                            [print(v) for v in result["variants"]]
        driver.close()
        f.close()
                


if __name__ == "__main__":
    asyncio.run(main())
