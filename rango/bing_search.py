import json
import urllib
import http.client
import certifi

def read_bing_key():
    bing_api_key = None

    try:
        with open('bing.key','r') as f:
            bing_api_key = f.readline()
    except:
        raise IOError('bing.key file not found')

    return bing_api_key


def run_query(search_terms):

    bing_api_key = read_bing_key()

    if not bing_api_key:
        raise KeyError("Bing Key Not Found")

    host = "api.cognitive.microsoft.com"
    path = "/bing/v7.0/search"

    headers = {'Ocp-Apim-Subscription-Key': bing_api_key}

    conn = http.client.HTTPSConnection(host)

    query = urllib.parse.quote(search_terms)

    conn.request("GET", path + "?q=" + query, headers=headers)

    response = conn.getresponse()

    headers = [k + ": " + v for (k, v) in response.getheaders()
               if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]

    result = response.read().decode("utf8")

    results = []

    json_response = json.loads(result)

    for result in json_response['webPages']['value']:
        results.append({'title': result['name'], 'link': result['url'], 'summary': result['snippet']})
    return results

def main():
    search_item = input("Enter your query: ")

    r = run_query(search_item)
    print(r)
if __name__ == '__main__':
    main()