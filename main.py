import os
import requests
import hmac
import hashlib
import base64
import time
import xml.etree.ElementTree as ET

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Your Amazon Access Keys
ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY')
SECRET_KEY = os.getenv('AMAZON_SECRET_KEY')
ASSOCIATE_TAG = os.getenv('AMAZON_ASSOCIATE_TAG')

# The Amazon Product Advertising API endpoint
ENDPOINT = 'webservices.amazon.com'
URI = "/onca/xml"

def create_signed_url(parameters):
    # Add necessary parameters
    parameters['Service'] = 'AWSECommerceService'
    parameters['AWSAccessKeyId'] = ACCESS_KEY
    parameters['AssociateTag'] = ASSOCIATE_TAG
    parameters['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Sort the parameters by key
    sorted_parameters = sorted(parameters.items())

    # Create the canonicalized query
    canonicalized_query = [f"{k}={v}" for (k, v) in sorted_parameters]
    canonicalized_query = '&'.join(canonicalized_query)

    # Create the string to sign
    string_to_sign = f"GET\n{ENDPOINT}\n{URI}\n{canonicalized_query}"

    # Calculate the signature
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(string_to_sign, 'utf-8'), digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature).decode()

    # Add the signature to the parameters
    parameters['Signature'] = signature

    # Create the signed URL
    signed_url = f"http://{ENDPOINT}{URI}?{canonicalized_query}&Signature={signature}"

    return signed_url

def search_items(keywords):
    # Define the parameters for the SearchItems operation
    parameters = {
        'Operation': 'ItemSearch',
        'SearchIndex': 'All',
        'Keywords': keywords,
        'ResponseGroup': 'ItemAttributes,Offers'
    }

    # Create the signed URL
    signed_url = create_signed_url(parameters)

    try:
        # Make the request to the Amazon Product Advertising API
        response = requests.get(signed_url)

        # Check if the request was successful
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        # The request returned an unsuccessful status code
        print(f"An HTTP error occurred: {e}")

        # Parse the error response
        error_root = ET.fromstring(response.content)
        error_code = error_root.find(".//Code").text

        if error_code == "RequestThrottled":
            # We've hit the rate limit
            print("Rate limit exceeded. Please wait and try again.")
            return None
        elif error_code in ["AWS.InvalidAccount", "AWS.MissingParameters"]:
            # There was an authentication error
            print("Authentication error. Please check your Amazon Access Key, Secret Key, and Associate Tag.")
            return None
        else:
            error_message = error_root.find(".//Message").text
            print(f"Error details: {error_message}")
            return None

    except requests.exceptions.RequestException as e:
        # A network error occurred
        print(f"A network error occurred: {e}")
        return None

    # Parse the XML response
    root = ET.fromstring(response.content)

    # Extract the information you need from the XML
    title_element = root.find(".//Title")

    if title_element is None:
        # The "Title" element wasn't found in the response
        print("The 'Title' element was not found in the response.")
        return None

    title = title_element.text

    # Return the parsed response
    return title
