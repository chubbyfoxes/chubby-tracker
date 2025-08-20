# sales_listener.py
import discord
from decimal import Decimal
from query import fetch_recent_sales, fetch_opensea_sales

def _format_price_ron(value):
    """
    Formatea realPrice asumiendo 18 decimales (wei-like).
    """
    try:
        ron = Decimal(str(value)) / Decimal(10**18)
        # Convert to string with all decimals, then trim trailing zeros but keep at least 2 decimals
        ron_str = format(ron, 'f')
        if '.' in ron_str:
            int_part, dec_part = ron_str.split('.')
            # Remove trailing zeros, but keep at least 2 decimals
            dec_part = dec_part.rstrip('0')
            if len(dec_part) < 2:
                dec_part = dec_part.ljust(2, '0')
            ron_str = f"{int_part}.{dec_part}"
        return f"{ron_str} RON"
    except Exception:
        return str(value)

def _format_price_eth(value):
    """
    Formatea precios en ETH (18 decimales).
    """
    try:
        eth = Decimal(str(value)) / Decimal(10**18)
        # Show up to 6 decimals for ETH, but keep at least 2
        eth_str = format(eth, 'f')
        if '.' in eth_str:
            int_part, dec_part = eth_str.split('.')
            # Keep up to 6 decimals, but trim trailing zeros, keep at least 2
            dec_part = dec_part[:6].rstrip('0')
            if len(dec_part) < 2:
                dec_part = dec_part.ljust(2, '0')
            eth_str = f"{int_part}.{dec_part}"
        return f"{eth_str} ETH"
    except Exception:
        return str(value)

async def notify_sale(channel: discord.abc.Messageable, sale: dict, collection_name: str, market: str, contract_address: str = None):
    assets = sale.get("assets", [])
    token = assets[0].get("token") if assets else {}
    typename = token.get("__typename") if token else "unknown"
    token_id = token.get("tokenId1155") if typename == "Erc1155" else token.get("tokenId721") if typename == "Erc721" else sale.get("tokenId", "¿?")
    name = token.get("name") or f"Token #{token_id}"

    # Imagen: primero la de Ronin, si no hay usa la de OpenSea o placeholder
    image = token.get("image") if token else ""
    if not image:
        image = assets[0].get("image_url", "")
    if not image:
        image = "https://via.placeholder.com/256?text=NFT"

    # Precio
    price_str = _format_price_ron(sale.get("realPrice")) if market == "ronin" else _format_price_eth(sale.get("price"))
    buyer = sale.get("matcher", sale.get("buyer", "¿?"))
    seller = sale.get("maker", sale.get("seller", "¿?"))
    tx_hash = sale.get("txHash")
    assets = sale.get("assets", [])
    quantity = 1
    if assets:
        token = assets[0].get("token", {})
        typename = token.get("__typename", "")
    if typename == "Erc1155":
        quantity = int(assets[0].get("quantity", 1))

    # Precio total (realPrice ya viene en WEI o base units)
    if market == "ronin":
        total_price = int(sale.get("realPrice", 0))
        unit_price = total_price // quantity if quantity > 0 else total_price
        price_total_str = _format_price_ron(total_price)   # ejemplo: "55.0000 RON"
        price_unit_str = _format_price_ron(unit_price)     # ejemplo: "0.5500 RON"
    else:
        total_price = int(sale.get("price", 0))
        unit_price = total_price // quantity if quantity > 0 else total_price
        price_total_str = _format_price_eth(total_price)
        price_unit_str = _format_price_eth(unit_price)


    # OpenSea item URL: https://opensea.io/item/ronin/{contract_address}/{token_id}
    item_url = f"https://opensea.io/item/ronin/{contract_address}/{token_id}" if contract_address and token_id else discord.Embed.Empty

    embed = discord.Embed(
        title=f"Chubby Fox #{token_id} has been sold!",
        url=item_url
    )

    if quantity > 1:
        embed.add_field(name="Sold for", value=f"{quantity} × {price_unit_str} = {price_total_str}", inline=False)
        embed.add_field(name="Quantity", value=str(quantity), inline=True)
    else:
        embed.add_field(name="Sold for", value=price_total_str, inline=False)

    # Shorten addresses for display (first 12 chars + ...)
    def short_addr(addr):
        return addr[:12] + '...' if len(addr) > 12 else addr

    buyer_url = f"https://opensea.io/{buyer}"
    seller_url = f"https://opensea.io/{seller}"
    # Show Buyer and Seller as two columns: title above, address below
    embed.add_field(name="From", value=f"[{short_addr(seller)}]({seller_url})", inline=True)
    embed.add_field(name="To", value=f"[{short_addr(buyer)}]({buyer_url})", inline=True)

   

    if image:
        embed.set_thumbnail(url=image)

    embed.set_footer(text=f"{market.capitalize()} • Sales notifier")

    await channel.send(embed=embed)


async def check_sales(
    session,
    channel,
    api_url,
    api_key,
    last_timestamp: int,
    collection_name: str,
    contract_or_slug: str,
    fetch_size: int,
    seen_tx_hashes: set,
    market: str = "ronin",
):
    """
    Pide ventas recientes y notifica las nuevas.
    """
    sales = await fetch_recent_sales(session, api_url, api_key, contract_or_slug, size=fetch_size) if market == "ronin" else await fetch_opensea_sales(session, api_url, api_key, contract_or_slug, last_timestamp)
    print(f"[INFO] Revisando {collection_name} en {market} - {len(sales)} ventas encontradas")

    new_sales = []
    for s in sales:
        ts = int(s.get("timestamp", 0))
        tx = s.get("txHash")
        if ts > last_timestamp or (ts == last_timestamp and tx and tx not in seen_tx_hashes):
            new_sales.append(s)

    if not new_sales:
        return last_timestamp

    new_sales.sort(key=lambda x: (int(x.get("timestamp", 0)), x.get("txHash") or ""))
    for s in new_sales:
        await notify_sale(channel, s, collection_name, market, contract_or_slug)
        tx = s.get("txHash")
        if tx:
            seen_tx_hashes.add(tx)
            if len(seen_tx_hashes) > 2000:
                for _ in range(len(seen_tx_hashes) - 1500):
                    seen_tx_hashes.pop()

    return max(int(s.get("timestamp", 0)) for s in new_sales)
