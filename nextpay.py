# // NextPay.IR Python Sample
# // docs : https://nextpay.org/nx/docs

# ////////////
# // step 1 //
# ////////////


import requests

url = "https://nextpay.org/nx/gateway/token"

api_key = "https://nextpay.org/nx/dashboard/stores/create"
payload=f'api_key={api_key}&amount=74250&order_id=85NX85s427&customer_phone=09121234567&custom_json_fields=%7B%20%22productName%22%3A%22Shoes752%22%20%2C%20%22id%22%3A52%20%7D&callback_uri=https%3A%2F%2FyourWebsite.com%2Fcallback'
headers = {
  'User-Agent': 'PostmanRuntime/7.26.8',
  'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)


# # ////////////
# # // step 5 //
# # ////////////

# import requests

# url = "https://nextpay.org/nx/gateway/verify"

# payload='api_key=b11ee9c3-d23d-414e-8b6e-f2370baac97b&amount=74250&trans_id=f7c07568-c6d1-4bee-87b1-4a9e5ed2e4c1'
# headers = {
#   'User-Agent': 'PostmanRuntime/7.26.8',
#   'Content-Type': 'application/x-www-form-urlencoded'
# }

# response = requests.request("POST", url, headers=headers, data=payload)

# print(response.text)