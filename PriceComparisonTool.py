from flask import Flask, request, jsonify
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


app = Flask(__name__)

class PriceComparator:
    def __init__(self, product_name):
        self.product_name = product_name
        self.amazon_url = f'https://www.amazon.in/s?k={self.product_name}'
        self.flipkart_url = f'https://www.flipkart.com/search?q={self.product_name}'
        self.lulu_url = f'https://www.luluhypermarket.com/en-ae/search?q={self.product_name.replace(" ", "+")}'
        self.gadget_url = f'https://www.gadgets360.com/search?searchtext={self.product_name.replace(" ", "+")}'
        self.jiomart_url = f'https://www.jiomart.com/search/{self.product_name.replace(" ", "+")}'
        self.shopthe_url = f'https://shoptheworld.in/s/{self.product_name.replace(" ","+")}'
        self.triveni_url = f'https://www.triveniworld.com/search?type=product&q={self.product_name.replace(" ","+")}'

    def fetch_price_with_selenium(self, url, price_selector, website_name):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install()) 
        driver = webdriver.Chrome(service=service, options=chrome_options)  

        driver.get(url)

        try:
            price_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, price_selector))
            )
            price = price_element.text.strip() if price_element else None
        except Exception as e:
            print(f"Error fetching price from {url}: {e}")
            price = None
        finally:
            driver.quit()

        return price, website_name

    def compare_prices(self):
        urls_and_selectors = [
            (self.amazon_url, 'span.a-price-whole', 'Amazon'),
            (self.flipkart_url, 'div.Nx9bqj._4b5DiR', 'Flipkart'),
            (self.lulu_url, 'p.product-price.has-icon span', 'Lulu'),
            (self.gadget_url, 'span.price-txt', 'Gadget360'),
            (self.jiomart_url, 'span.jm-heading-xxs.jm-mb-xxs', 'JioMart'),
            (self.shopthe_url, 'h4.priceStyle', 'ShopTheWorld'),
            (self.triveni_url, 'span.price-current', 'Triveni')
        ]

        prices = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            results = executor.map(self.fetch_price_with_selenium, *zip(*urls_and_selectors))

        for price, website in results:
            prices.append({"website": website, "price": price if price else "Price not found"})
        
        return prices


@app.route('/compare_prices', methods=['POST'])
def compare_prices():
    data = request.get_json()  # Expecting a JSON body with the 'product_name'
    
    if not data or 'product_name' not in data:
        return jsonify({"error": "Product name is required"}), 400
    
    product_name = data['product_name']
    price_comparator = PriceComparator(product_name)
    prices = price_comparator.compare_prices()
    
    return jsonify({
        "product_name": product_name,
        "prices": prices
    })


if __name__ == '__main__':
    app.run(debug=True,port=5006)
