
import discord
from decimal import Decimal
from query import fetch_recent_sales, fetch_opensea_sales

def _format_price_ron(value):
    try:
        ron = Decimal(str(value)) / Decimal(10**18)
        ron_str = format(ron, 'f')
        if '.' in ron_str:
            int_part, dec_part = ron_str.split('.')
            dec_part = dec_part.rstrip('0')
            if len(dec_part) < 2:
                dec_part = dec_part.ljust(2, '0')
            ron_str = f"{int_part}.{dec_part}"
        return f"{ron_str} RON"
    except Exception:
        return str(value)

async def notify_sale(channel, sale, collection_name, market, contract_address=None):
    if market == "ronin":
        assets = sale.get("assets", [])
        token = assets[0].get("token") if assets else {}
        typename = token.get("__typename") if token else "unknown"
        token_id = token.get("tokenId1155") if typename == "Erc1155" else token.get("tokenId721") if typename == "Erc721" else sale.get("tokenId", "¿?")
        image = token.get("image") if token else ""
        if not image:
            image = assets[0].get("image_url", "")
        if not image:
            image = "https://via.placeholder.com/256?text=NFT"
        price_str = _format_price_ron(sale.get("realPrice"))
        buyer = sale.get("matcher", sale.get("buyer", "¿?"))
        seller = sale.get("maker", sale.get("seller", "¿?"))
        quantity = 1
        if assets:
            token = assets[0].get("token", {})
            typename = token.get("__typename", "")
        if typename == "Erc1155":
            quantity = int(assets[0].get("quantity", 1))
        total_price = int(sale.get("realPrice", 0))
        unit_price = total_price // quantity if quantity > 0 else total_price
        price_total_str = _format_price_ron(total_price)
        price_unit_str = _format_price_ron(unit_price)
        item_url = f"https://opensea.io/item/ronin/{contract_address}/{token_id}" if contract_address and token_id else discord.Embed.Empty
    else:
        token_id = sale.get("tokenId", "¿?")
        image = sale.get("image") or "https://via.placeholder.com/256?text=NFT"
        buyer = sale.get("matcher", sale.get("buyer", "¿?"))
        seller = sale.get("maker", sale.get("seller", "¿?"))
        quantity = sale.get("quantity", 1)
        try:
            quantity = int(quantity)
        except Exception:
            quantity = 1
        total_price = int(sale.get("price", 0))
        unit_price = total_price // quantity if quantity > 0 else total_price
        symbol = "RON"
        if hasattr(sale, "get") and "payment" in sale and sale["payment"] and isinstance(sale["payment"], dict):
            symbol = sale["payment"].get("symbol", "RON")
        def format_price_symbol(amount):
            try:
                val = Decimal(str(amount)) / Decimal(10**18)
                val_str = format(val, 'f')
                if '.' in val_str:
                    int_part, dec_part = val_str.split('.')
                    dec_part = dec_part.rstrip('0')
                    if len(dec_part) < 2:
                        dec_part = dec_part.ljust(2, '0')
                    val_str = f"{int_part}.{dec_part}"
                return f"{val_str} {symbol}"
            except Exception:
                return f"{amount} {symbol}"
        price_total_str = format_price_symbol(total_price)
        price_unit_str = format_price_symbol(unit_price)
        contract_addr = sale.get("contract") or contract_address
        item_url = f"https://opensea.io/assets/ronin/{contract_addr}/{token_id}" if contract_addr and token_id else discord.Embed.Empty

    embed = discord.Embed(
        title=f"Chubby Fox #{token_id} has been sold!",
        url=item_url
    )
    if quantity > 1:
        embed.add_field(name="Sold for", value=f"{quantity} × {price_unit_str} = {price_total_str}", inline=False)
        embed.add_field(name="Quantity", value=str(quantity), inline=True)
    else:
        embed.add_field(name="Sold for", value=price_total_str, inline=False)
    def short_addr(addr):
        return addr[:12] + '...' if len(addr) > 12 else addr
    buyer_url = f"https://opensea.io/{buyer}"
    seller_url = f"https://opensea.io/{seller}"
    embed.add_field(name="From", value=f"[{short_addr(seller)}]({seller_url})", inline=True)
    embed.add_field(name="To", value=f"[{short_addr(buyer)}]({buyer_url})", inline=True)
    if image:
        embed.set_thumbnail(url=image)
    if market.lower() == "ronin":
        embed.set_footer(text="Ronin marketplace")
    else:
        embed.set_footer(text="Opensea")
    await channel.send(embed=embed)

async def check_sales(
    session,
    channel,
    api_url,
    api_key,
    last_timestamp,
    collection_name,
    contract_or_slug,
    fetch_size,
    seen_tx_hashes,
    market="ronin",
):
    sales = await fetch_recent_sales(session, api_url, api_key, contract_or_slug, size=fetch_size) if market == "ronin" else await fetch_opensea_sales(session, api_url, api_key, contract_or_slug, last_timestamp, fetch_size=fetch_size)
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
