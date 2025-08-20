# 🦊 Chubby Foxes Tracker

A Python-based bot for tracking **NFT sales and events** in the Chubby Foxes ecosystem, focusing on the **Chubby Foxes** collection (with plans to expand to more NFTs).

---

## 📌 Project Overview

**Features:**

- Automated polling of Ronin/OpenSea APIs (configurable interval).
- Discord notifications for new Chubby Foxes sales/events.
- Free-tier hosting on Google Cloud (24/7 uptime).

**Built with:**

- Python + aiohttp (async API calls).
- discord.py for Discord integration.
- GraphQL for Ronin queries.

---

## 🛠️ Key Features

| Feature              | Description                                                |
| -------------------- | ---------------------------------------------------------- |
| Configurable Polling | Default: 120 sec (to stay within GCP free tier limits).    |
| Efficient Tracking   | Fetches up to 100 events per call.                         |
| No Duplicates        | Stores last sales in `last_sales.json`.                    |
| Discord Alerts       | Formatted embeds with buyer/seller info, price, and links. |

---

## 📂 Files & Structure

```
chubby-tracker/
├── bot.py             # Main script (Discord bot + polling loop)
├── sales_listener.py  # Handles API queries & data processing
├── query.py           # Query helpers/utilities
├── test_env.py        # Environment/test helpers
├── images/
│   ├── image.png      # Project image/logo
│   └── image2.png     # Additional image asset
├── __init__.py        # Package marker
├── __pycache__/       # Python cache files
├── README.md          # This file
└── ...                # Other files (e.g., config, .env, .gitignore)
```

---

bash

## 🚀 Setup & Deployment

🔧 Local Setup
Clone the repo:

```bash
git clone https://github.com/chubbyfoxes/chubby-tracker.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔗 Resources

- 🦊 [Chubby Foxes Official Site](https://chubbyfoxes.xyz/)
- 🦊 [Chubby Foxes NFTs](https://marketplace.roninchain.com/collections/chubby-foxes)

---

## 💡 Future Improvements

- Add support for more Chubby Foxes NFTs and features.
- Optimize API polling efficiency.
- Multi-marketplace integration.

Contributions welcome! Open an issue or PR.

---

<div align="center">
	<strong>✨ P.S. ¡shout out to <span style="color:#e63946;">Pimmpi</span>! ✨</strong>
</div>
