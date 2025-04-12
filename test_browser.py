from playwright.async_api import async_playwright
import asyncio

async def get_item_info(item_locator):
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
            product_name = f"{product_name} ({aka_text})"

        return {
            'product_number': product_number,
            'product_name': product_name,
        }

async def get_all_items_info(page):
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
                item_info = await get_item_info(item)
                items_info.append(item_info)
            except Exception as e:
                print(f"Error processing item {i}: {str(e)}")
                items_info.append({
                    'product_number': 'ERROR',
                    'product_name': f"Item {i+1} - Error",
                    'error': str(e)
                })
        
        return items_info
    
async def hobby_db_lookup(page, sku, context):
    """Look up a product on HobbyDB by SKU."""
    url = "https://www.hobbydb.com/marketplaces/hobbydb/catalog_items?filters[q][0]="
    await page.goto(url + sku)

    # Get main item info
    main_item = page.locator('div.catalog-item-info').first
    await main_item.wait_for(state='attached', timeout=5000)
    info = await get_item_info(main_item)
    info['sku'] = sku  # Add the original SKU to the result
    
    # Check for variants
    variant_selector = main_item.locator('span[ng-if=" item.attributes.variantsCount > 1"] > a')
    if await variant_selector.count() > 0:
        href = await variant_selector.first.get_attribute('href')
        new_page = await context.new_page()
        await new_page.goto("https://www.hobbydb.com" + href)
        #await new_page.wait_for_load_state('networkidle')
        info["variants"] = await get_all_items_info(new_page)
        await new_page.close()
    
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
        return {
            'sku': sku,
            'error': str(e)
        }

async def main():
    skus = input("Enter SKUs separated by commas: ").strip().split(',')
    skus = [sku.strip() for sku in skus if sku.strip()]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Process SKUs with concurrency limit of 5
        semaphore = asyncio.Semaphore(5)
        
        async def limited_process(sku):
            async with semaphore:
                return await process_sku(browser, sku)
        
        tasks = [limited_process(sku) for sku in skus]
        results = await asyncio.gather(*tasks)
        
        # Print results
        for result in results:
            if 'error' in result:
                print(f"\nError processing SKU: {result['sku']}")
                print(f"Error: {result['error']}")
                print("-" * 40)
                continue
                
            print(f"\nSKU: {result['sku']}")
            print(f"Product Number: {result['product_number']}")
            print(f"Product Name: {result['product_name']}")
            
            # Check for AKA (alternative name)
            if '(' in result['product_name'] and ')' in result['product_name']:
                print("- Includes AKA information")
            
            if 'variants' in result and len(result['variants']) > 0:
                print(f"- Has {len(result['variants'])} variants:")
                for i, variant in enumerate(result['variants'], 1):
                    print(f"  Variant {i}:")
                    print(f"    Number: {variant.get('product_number', 'N/A')}")
                    print(f"    Name: {variant.get('product_name', 'N/A')}")
                    if 'error' in variant:
                        print(f"    Error: {variant['error']}")
                print("-" * 40)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
