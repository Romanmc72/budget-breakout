#!/usr/bin/env python3
"""
Description
-----------
Starting with one main program and going from there. I can soooo quickly scope
creep myself into a multi-month project, that I want to start simple and extend
as I go where I see needs extending.

So right now a simple single python script will do!
"""
import itertools
import random
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

import pandas as pd
from bokeh.plotting import figure, output_file, save, show
from bokeh.resources import INLINE
from bokeh.models import Span


def create_random_hex_color() -> str:
    """simply returns a random hex color value, it will change every time"""
    rand_smallint = lambda: random.randint(0, 255)
    return "#" + "".join(f"{rand_smallint():02X}" for _ in range(3)).lower()


def main(
    file_to_load: str,
    earliest_date: datetime = None,
    budgeted_income: int = None,
    budgeted_essentials: int = None,
    budgeted_nonessentials: int = None,
) -> None:
    """The main program that will spit out the graphs"""
    total_budgeted_expenses = (budgeted_essentials or 0) + (budgeted_nonessentials or 0)
    df = pd.read_csv(file_to_load)

    df = filter_out_noise(df)

    df["PyDate"] = df.Date.map(lambda d: datetime.strptime(d, "%m/%d/%Y"))
    if earliest_date:
        pass
    else:
        print("No earliest_date provided, defaulting to last 6 months...")
        six_months_ago = datetime.now(timedelta(days=6 * 30))
        earliest_date = datetime(six_months_ago.year, six_months_ago.month, 1)
    df = df[df.PyDate >= earliest_date]
    df["YearMonth"] = df.PyDate.map(lambda d: d.strftime("%Y-%m"))
    df["adjusted_amount"] = (
        df["Transaction Type"].map(lambda t: -1 if t == "debit" else 1) * df.Amount
    )
    categories_set = set(df.Category)
    essential_categories = set(
        [
            "Home Phone",
            "Tithes and Offerings",
            "Tuition",
            "Life Insurance",
            "Gas & Fuel",
            "Personal Care",
            "Veterinary",
            "Books & Supplies",
            "Groceries",
            "Utilities",
            "Mortgage & Rent",
            "Pet Food & Supplies",
            "Doctor",
            "Pets",
        ]
    )
    categories = list(set(categories_set))
    categories.sort()
    year_months = list(set(df.YearMonth))
    year_months.sort()
    essential_labels = ["Essential", "Non-Essential"]
    df["essentials"] = df.Category.map(
        lambda category: essential_labels[0]
        if category in essential_categories
        else essential_labels[1]
    )

    # Income chart
    income_df = df[df.adjusted_amount > 0]
    income_totals = income_df.groupby(["Category", "YearMonth"]).adjusted_amount.sum()
    income, income_categories = create_data_mapping(
        categories, year_months, income_totals, positives=True
    )
    income_plot = make_stacked_bar_chart(
        income,
        year_months,
        income_categories,
        "Income by category by month",
        line=budgeted_income,
    )
    save_html_and_show_graphs(income_plot, "./income.html", "Income")

    # Splits out costs by all, essential vs non essential, and the sub charts
    # just for those essential/non-essential categories
    cost_df = df[df.adjusted_amount < 0]
    cost_totals = cost_df.groupby(["Category", "YearMonth"]).adjusted_amount.sum()
    cost, sorted_cost_categories = create_data_mapping(
        categories, year_months, cost_totals, positives=False
    )
    cost_plot = make_stacked_bar_chart(
        cost,
        year_months,
        sorted_cost_categories,
        "All Costs by category by month",
        line=total_budgeted_expenses,
    )
    save_html_and_show_graphs(cost_plot, "./cost.html", "Costs")

    essentials_breakout_totals = cost_df.groupby(
        ["essentials", "YearMonth"]
    ).adjusted_amount.sum()
    essentials_breakout_cost, sorted_eb_cost_categories = create_data_mapping(
        essential_labels, year_months, essentials_breakout_totals, positives=False
    )
    essentials_breakout_cost_plot = make_stacked_bar_chart(
        essentials_breakout_cost,
        year_months,
        sorted_eb_cost_categories,
        "Essential Vs Non-Essential by month",
        line=total_budgeted_expenses,
    )
    save_html_and_show_graphs(
        essentials_breakout_cost_plot,
        "./essentials_breakout.html",
        "Essentials Breakout",
    )

    essentials_df = cost_df[cost_df.essentials == essential_labels[0]]
    essentials_totals = essentials_df.groupby(
        ["Category", "YearMonth"]
    ).adjusted_amount.sum()
    essentials, essential_categories = create_data_mapping(
        categories, year_months, essentials_totals, positives=False
    )
    essentials_plot = make_stacked_bar_chart(
        essentials,
        year_months,
        essential_categories,
        "Essential Breakout by month",
        line=budgeted_essentials,
    )
    save_html_and_show_graphs(essentials_plot, "./essentials.html", "Essentials")

    non_essentials_df = cost_df[cost_df.essentials == essential_labels[1]]
    non_essentials_totals = non_essentials_df.groupby(
        ["Category", "YearMonth"]
    ).adjusted_amount.sum()
    non_essentials, non_essential_categories = create_data_mapping(
        categories, year_months, non_essentials_totals, positives=False
    )
    non_essentials_plot = make_stacked_bar_chart(
        non_essentials,
        year_months,
        non_essential_categories,
        "Non-Essential Breakout by month",
        line=budgeted_nonessentials,
    )
    save_html_and_show_graphs(
        non_essentials_plot, "./non_essentials.html", "Non Essentials"
    )
    return df


def save_html_and_show_graphs(plot, filename, title):
    output_file(filename=filename, title=title)
    save(plot, filename=filename, resources=INLINE)
    show(plot)


def filter_out_noise(df):
    """
    Description
    -----------
    Removing the category and transaction type pairs that are not useful to
    see in the analysis built by this program.

    Params
    ------
    :df: pd.DataFrame
    The input dataframe

    Return
    ------
    pd.DataFrame
    The filtered dataframe with the noise removed
    """
    # Remove transfers because that is just credit card payments and moving $
    # from checking to saving or vice versa
    df = df[(df.Category != "Transfer")]
    df = df[df.Category != "Credit Card Payment"]

    # Remove these because they are just payments on the mortgage
    df = df[(df.Category != "Loan Payment") | (df["Transaction Type"] != "credit")]
    return df


def create_data_mapping(categories, year_months, totals, positives=False):
    data = defaultdict(list)
    for pair in itertools.product(year_months, categories):
        year_month = pair[0]
        category = pair[1]
        try:
            value = totals[(category, year_month)]
            if positives and value > 0:
                data[category].append(value)
            elif not positives and value < 0:
                data[category].append(-1 * value)
            else:
                data[category].append(0)
        except KeyError:
            data[category].append(0)
    sorted_by_total = OrderedDict(
        sorted(
            [(k, v) for k, v in data.items()],
            key=lambda row: sum(row[1]),
            reverse=True,
        )
    )
    sorted_categories = list(sorted_by_total.keys())
    sorted_by_total.update({"year-months": year_months})
    return sorted_by_total, sorted_categories


def make_stacked_bar_chart(data, year_months, categories, title, line=None):
    plot = figure(
        x_range=year_months,
        title=title,
        tools="hover",
        tooltips="$name : @$name{$0,0.00}",
    )
    plot.vbar_stack(
        categories,
        x="year-months",
        color=[create_random_hex_color() for _ in range(len(categories))],
        source=data,
    )
    plot.y_range.start = 0
    plot.x_range.range_padding = 0.1
    plot.xgrid.grid_line_color = None
    plot.axis.minor_tick_line_color = None
    plot.outline_line_color = None
    if line:
        horizontal_line = Span(
            location=line, dimension="width", line_color="red", line_width=3
        )
        plot.renderers.extend([horizontal_line])
    return plot


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file_to_upload", help="The location of the mint transactions.csv to use"
    )
    three_months_ago = datetime.now() - timedelta(days=90)
    start_of_three_months_ago = datetime(
        three_months_ago.year,
        three_months_ago.month,
        1,
    )
    parser.add_argument(
        "--earliest_date",
        type=lambda x: datetime.fromisoformat(x),
        required=False,
        default=start_of_three_months_ago,
        help="The earliest date to include in the charts, defaults to the start of 3 months ago",
    )
    parser.add_argument(
        "--budgeted_income",
        type=int,
        required=False,
        default=None,
        help="The amount of income you budgeted for",
    )
    parser.add_argument(
        "--budgeted_essentials",
        type=int,
        required=False,
        default=None,
        help="The amount of essential expenses you budgeted for",
    )
    parser.add_argument(
        "--budgeted_nonessentials",
        type=int,
        required=False,
        default=None,
        help="The amount of non-essential expenses you budgeted for",
    )
    args = parser.parse_args()
    main(
        args.file_to_upload,
        args.earliest_date,
        args.budgeted_income,
        args.budgeted_essentials,
        args.budgeted_nonessentials,
    )
