import os
import time
import argparse

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def render_html_to_png(input_html, output_png, width=1600, height=900, scale=2, wait=2):
    input_path = os.path.abspath(input_html)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input HTML not found: {input_path}")

    url = 'file://' + input_path.replace('\\', '/')

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    # set the window large to get high-res; we'll use deviceScaleFactor via CDP
    chrome_options.add_argument(f'--window-size={width*scale},{height*scale}')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # set device scale (DPR) for higher pixel density
        try:
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'mobile': False,
                'width': width,
                'height': height,
                'deviceScaleFactor': scale,
            })
        except Exception:
            # not fatal
            pass

        driver.get(url)
        # wait for full load; leaflet loads tiles asynchronously
        time.sleep(wait)

        # attempt to enlarge map container to requested size
        try:
            driver.execute_script("document.getElementsByClassName('folium-map')[0].style.width=arguments[0]+'px'; document.getElementsByClassName('folium-map')[0].style.height=arguments[1]+'px';", width, height)
        except Exception:
            pass

        time.sleep(0.8)

        png = driver.get_screenshot_as_png()
        with open(output_png, 'wb') as f:
            f.write(png)
        print('Wrote PNG:', output_png)

    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default='tashu_presentation_map.html')
    parser.add_argument('--output', '-o', default='tashu_presentation_map.png')
    parser.add_argument('--width', type=int, default=1600)
    parser.add_argument('--height', type=int, default=900)
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--wait', type=float, default=2.0)
    args = parser.parse_args()

    render_html_to_png(args.input, args.output, width=args.width, height=args.height, scale=args.scale, wait=args.wait)


if __name__ == '__main__':
    main()
