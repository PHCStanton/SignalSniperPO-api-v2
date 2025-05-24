## Libraries
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re
import os

## Global Variables
global driver
global wait
global balance
global DoTrade
global Call

DoTrade = False
Call = "None"

## Page
def Open_page():
    global driver
    driver = uc.Chrome()
    try:
        url = "https://pocketoption.com/en/cabinet/demo-quick-high-low/"
        driver.get(url)
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Page successfully opened!")

## Locate the Google Button
def Locate_Button():
    global driver
    global wait
    try:
        wait = WebDriverWait(driver, 15)  # Timeout of 15 seconds
        google_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'social-btn--gp')]")))
        print("Login with Google button located.")
        google_button.click()
        print("Login with Google button clicked!")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Button_located_clicked_Sucessfully")

## Fill the E-mail
def Fill_E_mail():
    global driver
    global wait
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
        print("Email input located.")
        email_input.clear()
        # CUSTOMIZE: Replace with your actual email address
        email_input.send_keys("your.email@gmail.com")
        email_input.send_keys(Keys.ENTER)
        time.sleep(5)
        print("Email entered.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("E_Mail_Enter_and_send_sucessfully")

## Send The Password
def Send_the_Password():
    global driver
    global wait
    try:
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        print("Password input located.")
        password_input.clear()
        # CUSTOMIZE: Replace with your actual password
        password_input.send_keys("your_secure_password")
        password_input.send_keys(Keys.ENTER)
        print("Password entered.")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Password_Enter_and_Send_Sucessfully")

## Shift To Demo Account
def Demo_Account():
    global driver
    global wait
    try:
        dropdown_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'balance-info-block__arrow')]"))
        )
        dropdown_button.click()
        print("Dropdown button clicked!")
        # Step 9: Wait for the "Quick Trading Demo" button to be visible
        quick_trade_demo_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'balance-item__label') and text()='Quick Trading Demo']"))
        )
        print("Quick Trading Demo button located.")
        quick_trade_demo_button.click()
        print("Quick Trading Demo button clicked!")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Shift To Demo Account Sucessfully")

## Buy 
def Buy():
    global driver
    global wait
    try:
        buy_button = wait.until(
           EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'switch-state-block__in')]//span[contains(text(), 'Buy')]"))
          )
        print("Buy button located.")
        # Step 12: Click the "Buy" button
        buy_button.click()
        print("Buy button clicked!")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Buy Button Clicked SucessFully")

## Sell
def Sell():
    global driver
    global wait
    try:
        sell_button = wait.until(
           EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'switch-state-block__in')]//span[contains(text(), 'Sell')]"))
        )
        print("Sell button located.")
        # Step 14: Click the "Sell" button
        sell_button.click()
        print("Sell button clicked!")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Sell Button Clicked SucessFully")

## Type of Trade
def Type_of_Trade():
    global driver
    global wait
    try:
        type_of_trade_button = wait.until(
           EC.element_to_be_clickable((By.XPATH, "//a[@class='pair-number-wrap']"))
        )
        type_of_trade_button.click()
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Type of Trade Button Clicked")

## Stock
def Stock(a):
    global driver
    global wait
    try:
        stock_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'assets-block__nav-item--stock')]"))
        )
        stock_button.click()
        # Step 17: Iterate through the stock list, click each item, and stop after specified number of stocks
        stock_items = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class, 'alist-stock')]//li/a"))
        )
        # Limit the number of stocks to click
        max_stocks_to_click = a
        for i, stock in enumerate(stock_items):
            if i >= max_stocks_to_click:
                break
            stock_name = stock.text.strip()
            print(f"Clicking on stock {i + 1}: {stock_name}")
            stock.click()
            time.sleep(5)  # Wait for 5 seconds before moving to the next stock
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Stock Selected")

## Printing The Balance
def Balance():
    global driver
    global wait
    global balance
    try:
        balance_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'balance-info-block')]"))
        )
        print("Balance button located.")
        # Step 19: Print the demo balance
        demo_balance = balance_button.text.strip()
        balance = demo_balance
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Balance_Selected")

## Curriencies
def Curriencies(a):
    global driver
    global wait
    try:
        currencies_button = wait.until(
        EC.element_to_be_clickable((By.XPATH,"//a[contains(@class, 'assets-block__nav-item--currency')]")))
        currencies_button.click()
        # Locate the list of currencies and iterate through the specified number
        currency_items = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class, 'alist-currency')]//li/a"))
        )
        # Limit the number of currencies to click
        max_currencies_to_click = a
        for i, currency in enumerate(currency_items):
            if i >= max_currencies_to_click:
                break
            currency_name = currency.text.strip()
            print(f"Clicking on currency {i + 1}: {currency_name}")
            currency.click()
            time.sleep(5)  # Wait for 5 seconds before moving to the next currency
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Curriencies Selected")

## CryptoCurriencies
def Crypto(a):
    global driver
    global wait
    try:
        crypto_button = wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class, 'assets-block__nav-item--cryptocurrency')]")))
        crypto_button.click()
        # Locate the list of cryptocurrencies and iterate through the specified number
        crypto_items = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class, 'alist-cryptocurrency')]//li/a")))
        max_crypto_to_click = a
        for i, crypto in enumerate(crypto_items):
            if i >= max_crypto_to_click:
                break
            crypto_name = crypto.text.strip()
            print(f"Clicking on cryptocurrency {i + 1}: {crypto_name}")
            crypto.click()
            time.sleep(5)
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Crypto Selected")

## Commodities
def Commodities(a):
    global driver
    global wait
    try:
        commodities_button = wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class, 'assets-block__nav-item--commodity')]")))
        commodities_button.click()
        # Locate the list of commodities and iterate through the specified number
        commodities_items = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class, 'alist-commodity')]//li/a")))
        max_commodities_to_click = a
        for i, commodity in enumerate(commodities_items):
            if i >= max_commodities_to_click:
                break
            commodity_name = commodity.text.strip()
            print(f"Clicking on commodity {i + 1}: {commodity_name}")
            commodity.click()
            time.sleep(5)
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Commodities Selected")

## Change Amount
def Amount():
    global driver
    global wait
    try:
        change_amount_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='block__control control']//input[@type='text']")))
        change_amount_button.clear()
        # CUSTOMIZE: Changed trade amount from 10 to 20
        change_amount_button.send_keys("20")
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Amount_Set_Successfully")

## Refresh
def Refresh():
    global driver
    global wait
    try:
        driver.refresh()
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Refresh Successfully")

## Real_Account
def Real_Account():
    global driver
    global wait
    try:
        dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'balance-info-block__arrow')]")))
        dropdown_button.click()
        # Step 26: Locate the "Quick Trading Real" button and click it
        quick_trade_real_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'balance-item__label') and text()='Quick Trading Real']")))
        quick_trade_real_button.click()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Shifted To Real Account")

## Time Remaining
def time_to_seconds(time_string):
    try:
        minutes, seconds = map(int, time_string.split(":"))
        total_seconds = minutes * 60 + seconds
        return total_seconds
    except ValueError:
        return 125

def Time():
    global driver
    global wait
    time = 10
    try:
        # Wait for the time element to be present
        time_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='item-row']/div[2]"))
        )
        action_time = time_element.text.strip()
        time = time_to_seconds(action_time)
        print("--------------------------")
        print(f"Time : {action_time}")
        print("--------------------------")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Time_Displayed_Successfully")
        return time

def extract_balance(data: str) -> float:
    match = re.search(r'[\d,]+\.\d+', data)
    if match:
        balance_str = match.group()  
        return float(balance_str.replace(',', ''))  
    return 0.0  # Return 0.0 instead of None to ensure a float is always returned

def Model():
    global balance
    global Call
    global DoTrade
    P_L = 0
    ## balance is the global variable that contain that is update after the balance call
    Balance()
    balance_before = extract_balance(balance)
    print("\n" * 1)
    print("Balance in float...::", balance_before)
    k = 0
    while(1):
        print("Iteration No.... :::", k)
        k = k + 1
        # CUSTOMIZE: Changed from 3 to 2 attempts for more conservative trading
        for i in range(2):
            print("\n" * 1)
            check = True
            print("Buying ..........................::: ", i)
            Buy()
            time.sleep(5)
            time.sleep(Time() + 5)
            P_L = 0
            Balance()
            print("-------------------------------")
            time.sleep(5)
            balance_after = extract_balance(balance)
            P_L = balance_after - balance_before 
            print("Balance Before.....:::", balance_before)
            balance_before = balance_after
            print("Balance After.....:::", balance_after)
            print("P_L----value ::: ", P_L)
            if P_L < 0:
                DoTrade = False
                break
            elif i == 0 and P_L > 0:
                Call = "Buy"
                DoTrade = True
                break
            elif P_L > 0:
                continue
        if DoTrade == True:
            break
        # CUSTOMIZE: Changed from 3 to 2 attempts for more conservative trading
        for i in range(2):
            print("\n" * 1)
            check = True
            print("Selling ..........................::: ", i)
            Sell()
            time.sleep(5)
            time.sleep(Time() + 5)
            P_L = 0
            Balance()
            print("-------------------------------")
            time.sleep(5)
            balance_after = extract_balance(balance)
            P_L = balance_after - balance_before 
            print("Balance Before.....:::", balance_before)
            balance_before = balance_after
            print("Balance After.....:::", balance_after)
            print("P_L----value ::: ", P_L)
            if P_L < 0:
                DoTrade = False
                break
            elif i == 0 and P_L > 0:
                Call = "Sell"
                DoTrade = True
                break
            elif P_L > 0:
                continue
        if DoTrade == True:
            break

# Main execution loop
def main():
    global DoTrade
    global Call
    count = 0
    
    while True:
        if count == 0:
            print("Page is Opening ........")
            time.sleep(2)
            os.system('cls')
            Open_page()
            os.system('cls')
            count = count + 1
            
        if count == 1:
            print("Entering the Credentials ........")
            time.sleep(2)
            Locate_Button()
            Fill_E_mail()
            Send_the_Password()
            os.system('cls')
            count = count + 1
            
        if count == 2:
            print("Shifting To Demo .........")
            time.sleep(2)
            Refresh()
            Demo_Account()
            os.system('cls')
            count = 3
            
        if DoTrade == False:
            print("Applying The Model ......")
            time.sleep(2)
            Model()
            print("Model Call :: ", Call)
            os.system('cls')
            
        if DoTrade == True:
            print("Doing Real Trade Shifting To Real Account .........")
            Refresh()
            # CUSTOMIZE: Uncommented to enable real trading
            Real_Account()
            os.system('cls')
            
            if Call == "Buy":
                print("Buy call by the Model")
                Buy()
                time.sleep(Time() + 5)
                os.system('cls')
                DoTrade = False
                Call = "None"
                count = 3
                
            if Call == "Sell":
                print("Sell call by the Model")
                Sell()
                time.sleep(Time() + 5)
                os.system('cls')
                DoTrade = False
                Call = "None"
                count = 3

# Example usage of individual functions
def test_functions():
    # Open_page()
    # Locate_Button()
    # Fill_E_mail()
    # Send_the_Password()
    # Demo_Account()
    # Buy()
    # Time()
    # Sell()
    # Type_of_Trade()
    # CUSTOMIZE: Changed from 8 to 5 stocks
    # Stock(5)
    # Balance()
    # print(balance)
    # CUSTOMIZE: Changed from 8 to 10 currencies
    # Curriencies(10)
    # CUSTOMIZE: Changed from 8 to 5 cryptocurrencies
    # Crypto(5)
    # CUSTOMIZE: Changed from 4 to 3 commodities
    # Commodities(3)
    # Amount()
    # Refresh()
    # Real_Account()
    pass

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
