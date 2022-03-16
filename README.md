# Web App: Trade Evaluation
[**Application Features**](#features)
| [**Requirements**](#requirements)
| [**Project Components**](#components)
| [**Resources and Inspirations**](#resources-and-inspirations)
| [**Hire Me**](#hire-me)

- I started investing on stock market 8 years ago and always wanted to make a comprehensive assessment of my portfolio performance. However, the only thing my broker could provide was the status quo of my portfolio and its holdings. Not much has changed until today.
- Sometimes, I also learn from somewhere very interesting investment strategies and stock picks but did not have a tool to keep track their performance for future usage.
- Today, with enough technical skills, I want to build an application that enables investors to manage hypothetical portfolios, experiment investment strategies, and automate their risks/returns performance assessment.
- Beside the above motivation, I also consider [Trade Evaluation](https://sphanfinance.com/1) a means of demonstrating my technical skills and financial knowledge to the recruiters.


### Table of Contents
* [Application Features](#features)
* [Requirements](#requirements)
* [Project components](#components)
* [Resources and Inspirations](#resources-and-inspirations)
* [Hire Me](#hire-me)

---
## Features

**1. Log in with demonstration account:** If you are a visitor and just want to know how the features look like, go to log in page and use the account that has been set up for demonstration purpose. 
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/login.gif)

**2. Three markets supported:** U.S, Germany, Vietnam.
**3. Get stock quote:** select the market, enter the stock symbol (in Bloomberg standard) and hit "Quote" to see more details. Quote can be used to check whether a symbol is valid.
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/quote.gif)

**4. Make hypothetical trades:** Select buy/sell, choose the symbol, type in volume, and hit "Buy/Sell".
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/trade.gif)

**5. Review current status of portfolios:** individual holding level and aggregate portfolio level.
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/portfolio.gif)

**6. See transaction history and filter it by market.**
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/history.gif)

**7. Portfolio performance evaluation:** select market to see how net asset value grew, then select a respective benchmark to compare portfolio returns against.
![image](https://github.com/sonpnt/Trade-Evaluation_WebApp/blob/main/static/images/evaluation.gif)

Try those features now: [sphanfinance.com](https://sphanfinance.com/login)

## Requirements
- Python 2.7 or above.
- HTTP Server (e.g. Google Cloud server)
- MySQL

## Components
### Data APIs:

- U.S. and German markets: [IEX](https://iextrading.com/developer), [Yahoo Finance](https://www.yahoofinanceapi.com/), [Bloomberg](https://www.bloomberg.com/)
- Vietnam market: [Saigon Securities Inc. (SSI)](https://www.ssi.com.vn/en), [VietDragon Securities Corp. (VDS)](https://www.vdsc.com.vn/en/home.rv) 

✍️ In order to minimize the database that needs storing and to save deployment costs, I only store data related to users and query market data from third-paty sources. This requires me to compromise the application performance a bit but I still managed to optimize data processing algorithm and limit reponse time to less than 20s for the most complicated requests.

### Logic codes
The logic part of the app is written using Python Flask, a light-weight and easy-to-use web development package. Since I am not a professional web developer, using Python enable me to focus on my strengths in building algorithms and data analytics while minimizing complexity of the code for the web server. This logic part comprises of 3 python files: `app.py`, `evaluation.py`, and `helpers.py`.
1. `app.py`: Focuses on handling requests from client side, storing client-related data (e.g. their credentials, transaction data).
2. `evaluation.py`: Focuses on querying time-series data from external APIs to support the core-function performance evaluation of the application.
3. `helpers.py`: Provides functions to request basic data from APIs, perform analyses, and other logical tasks to support the main file `app.py`. 

### Database
A sample file `finance.db` is included above to give you a perspective of how the relational database in this case looks like.

## Resources and Inspirations
- :blue_book: Computational thinking courses - Mannheim university.
- :book: Introduction to Computer Science (CS50) - [Harvard University](https://cs50.harvard.edu/x/2022/).
- :cloud: Google Cloud Tech - [Youtube Channel](https://www.youtube.com/user/googlecloudplatform).
- :gift: Free Stock Data for Python Using Yahoo Finance API - [Towards Data Science](https://towardsdatascience.com/free-stock-data-for-python-using-yahoo-finance-api-9dafd96cad2e).

## Hire me
Looking for a finance professional who is interested in and capable of using programming to build financial and data analytics apps? Get in touch: [pnthanhson.ftu2@gmail.com](mailto:pnthanhson.ftu2@gmail.com)
