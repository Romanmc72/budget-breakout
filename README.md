# Budget Stuff

I have a budgeting thing that I do every quarter or so (depending on when I can make time) and it involves spitting out my list of all Mint transactions to a csv then ingesting and processing that CSV to render various visualizations off of it. I am going to take the time here to formally write that all out as a more interactive program which I can run and rerun in the future to more easily prep the data and identify the transactions that are incorrectly categorized. This is far more easily said than done, and it has been a while so I will just write out some of the steps here in the readme and probably revisit this over time as I do it more and more often.

## High Level Steps

- Filter to Last "X" months
- Drop "Notes" column
    - Remove rows for credit card payments
    - Remove non-venmo bank transfers
    - Find the incorrect categories and fix those
- Change the "debit" rows to have amount = amount * -1
- Get all of the categories and all of the months together and make a table of their cartesian product
- Sum up the totals by those category-year-month buckets (some may be zero)
- calculate average spend by category byt month over the last "X" months
- Make charts
    - Preferably ones that can drill down
- Profit
