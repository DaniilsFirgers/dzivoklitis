# Dzīvoklitis

The app scrapes real estate ads data from from multiple sources, keeps track of price changes and notifies registered telegram users of any new updates based on their defined filters.

Currently the following sources are supported:

- [ss.lv](https://www.ss.com)
- [city24.lv](https://https://www.city24.lv)
- [pp.lv](https://pp.lv)

## TODO

- [ ] Add filters to db, currently with an sql command
- [ ] Create a cron for Postgres database dump (currently it is a cli command on the server)
- [ ] Introduce more robust error handling
- [ ] If possible, add house type?
- [ ] Move scraper settings from settings.json file to the database + adjust queries
- [ ] Add Rigas rajons and Jurmala
- [ ] Add zip.lv scraper
- [ ] Add varianti.lv scraper
- [ ] Add dalder.lv scraper
- [ ] Add dzivokliunmajas.lv scraper
- [ ] Create a separate task to populate locations for SS scraper
