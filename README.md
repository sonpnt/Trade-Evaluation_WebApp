# WebApp: Trade Evaluation
[**Application Features**](#features)
| [**Requirements**](#requirements)
| [**Project components**](#components)

- I started investing on stock market 8 years ago and always wanted to make a comprehensive assessment of my portfolio performance. However, the only thing my broker could provide was the status quo of my portfolio and its holdings. Not much has changed until today.
- Sometimes, I also learn from somewhere very interesting investment strategies and stock picks but did not have a tool to keep track their performance for future usage.
- Today, with enough technical skills, I want to build an application that enables investors to manage hypothetical portfolios, experiment investment strategies, and automate their risks/returns performance assessment.
- Beside the above motivation, I also consider [Trade Evaluation](https://sphanfinance.com/1) a means of demonstrating my technical skills and financial knowledge to the recruiters.


### Table of Contents
* [Application Features](#features)
* [Requirements](#requirements)
* [Project components](#components)

---
## Features

1. Log in with demonstration account: If you are a visitor and just want to know how the features look like, go to log in page and use the account that has been set up for demonstration purpose. 
![image](https://scontent-frx5-2.xx.fbcdn.net/v/t39.30808-6/275610810_5041581762552081_1079274052069687686_n.jpg?_nc_cat=1&ccb=1-5&_nc_sid=2c4854&_nc_ohc=Tz-zqT_EGRQAX_b8558&_nc_ht=scontent-frx5-2.xx&oh=00_AT8BJ1TunBWLjXinEkpsAsvyurx-7fg6xE8tvbIK_o6PCw&oe=6233D7F7)

2. Three markets supported: U.S, Germany, Vietnam
3. Get stock quote: select the market, enter the stock symbol (in Bloomberg standard) and hit "Quote" to see more details. Quote can be used to check whether a symbol is valid.
4. Make hypothetical trades: Select buy/sell, choose the symbol, type in volume, and hit "Buy/Sell"
5. Review current status of portfolios: individual holding level and aggregate portfolio level
6. See transaction history and filter it by market
7. Portfolio performance evaluation: select market to see how net asset value grew, then select a respective benchmark to compare portfolio returns against

Try it now: [sphanfinance.com](https://sphanfinance.com/)

## Requirements
- Python 2.7 or above.
- HTTP Server (e.g. Google Cloud server)
- MySQL

## Components
1. Data APIs: 
- U.S. and German markets: [IEX](https://iextrading.com/developer), [Yahoo Finance](https://www.yahoofinanceapi.com/), [Bloomberg](https://www.bloomberg.com/)
- Vietnam market: [Saigon Securities Inc. (SSI)](https://www.ssi.com.vn/en), [VietDragon Securities Corp. (VDS)](https://www.vdsc.com.vn/en/home.rv) 
2. 
