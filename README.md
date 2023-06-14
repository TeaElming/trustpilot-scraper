# trustpilot-scraper

Minimal Python scraper to download reviews from Trustpilot per rating (1-5 star system) for all companies in all categories from Trustpilot.

Fully functional during the summer of 2023 but sparsely documented. No promises made going forward. Default run results in a tsv file in dir ```data``` with columns text and rating. In this case, reviews will be collected for all Trustpilot categories and all companies regardless of star rating. This can, however, be easily modified in the code if you follow the print statements. Script can be run as-is with no user input. Some throttling is implemented and could probably be decreased for better run time.

The scraper was initially created to complete the Scandinavian sentiment dataset [ScandiSent](https://github.com/timpal0l/ScandiSent) with neutral examples, represented here by 3 star ratings. This was done in order to create a robust multi-class transformer sentiment model in Swedish (with labels neg/neu/pos). Link to public model will be published shortly.