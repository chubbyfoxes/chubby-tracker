
import aiohttp

async def fetch_recent_sales(session, api_url, api_key, contract_address, size=10, from_=0):
  query = """
  query RecentSales($tokenAddress: String!, $from: Int!, $size: Int!) {
    recentlySolds(from: $from, size: $size, tokenAddress: $tokenAddress) {
    results {
      assets { token { __typename ... on Erc1155 { tokenId1155: tokenId name image } ... on Erc721 { tokenId721: tokenId name image } } quantity }
      maker matcher realPrice timestamp txHash
    }
    }
  }
  """
  variables = {"tokenAddress": contract_address, "from": from_, "size": size}
  headers = {"Content-Type": "application/json"}
  if api_key:
    headers["x-api-key"] = api_key
  async with session.post(api_url, json={"query": query, "variables": variables}, headers=headers) as r:
    if r.status != 200:
      raise RuntimeError(f"GraphQL HTTP {r.status}: {await r.text()}")
    data = await r.json()
  if "errors" in data:
    raise RuntimeError(f"GraphQL errors: {data['errors']}")
  return data["data"]["recentlySolds"]["results"]

async def fetch_opensea_sales(session, api_url, api_key, slug_or_contract, last_checked, fetch_size=9):
  headers = {"accept": "application/json", "x-api-key": api_key}
  url = f"https://api.opensea.io/api/v2/events/collection/{slug_or_contract}"
  params = {"event_type": "sale", "limit": fetch_size}
  async with session.get(url, headers=headers, params=params) as r:
    if r.status != 200:
      raise RuntimeError(f"OpenSea HTTP {r.status}: {await r.text()}")
    data = await r.json()
  sales = []
  for event in data.get("asset_events", []):
    nft = event.get("nft", {})
    payment = event.get("payment", {})
    try:
      price = int(payment.get("quantity", 0))
    except Exception:
      price = 0
    try:
      quantity = int(event.get("quantity", 1))
    except Exception:
      quantity = 1
    sales.append({
      "tokenId": nft.get("identifier", "¿?"),
      "price": price,
      "maker": event.get("seller", "¿?"),
      "matcher": event.get("buyer", "¿?"),
      "timestamp": event.get("event_timestamp", 0),
      "txHash": event.get("transaction", ""),
      "image": nft.get("image_url", ""),
      "quantity": quantity,
      "contract": nft.get("contract", ""),
      "payment": payment
    })
  sales.sort(key=lambda x: int(x.get("timestamp", 0)), reverse=True)
  return sales