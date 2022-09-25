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
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
from bokeh.plotting import figure, show

HEX_COLORS = [
    '#2803aa',
    '#1e1e26',
    '#b0a1f9',
    '#426538',
    '#79eb1d',
    '#6e63d1',
    '#01b94d',
    '#b69cad',
    '#8bbcc5',
    '#577dca',
    '#f0a1f4',
    '#b65bb3',
    '#36a8c3',
    '#ccb274',
    '#24c12d',
    '#65b48f',
    '#11748c',
    '#4a4a47',
    '#d2cb93',
    '#f62209',
    '#74795',
    '#75a047',
    '#a53921',
    '#20e341',
    '#ffb8d8',
    '#46c557',
    '#9dc0e0',
    '#0be63b',
    '#396b4f',
    '#f75182',
    '#0603ee',
    '#340bf7',
    '#1424b2',
    '#3caebc',
    '#9320ae',
    '#fa8115',
    '#780d9e',
    '#8b7edc',
    '#ce4315',
    '#b4a185',
    '#37d58d',
    '#2e7fe',
]


def main(file_to_load: str, earliest_date: datetime = None) -> None:
    """"""
    df = pd.read_csv(file_to_load)
    # Remove transfers because that is just credit card payments and moving $
    # from checking to saving or vice versa
    df = df[df.Category != 'Transfer']
    df['PyDate'] = df.Date.map(lambda d: datetime.strptime(d, "%m/%d/%Y"))
    if earliest_date:
        pass
    else:
        print("No earliest_date provided, defaulting to last 6 months...")
        six_months_ago = datetime.now(timedelta(days=6 * 30))
        earliest_date = datetime(six_months_ago.year, six_months_ago.month, 1)
    df = df[df.PyDate >= earliest_date]
    df['YearMonth'] = df.PyDate.map(lambda d: d.strftime("%Y-%m"))
    df['adjusted_amount'] = df['Transaction Type'].map(
        lambda t: -1 if t == 'debit' else 1
    ) * df.Amount
    categories_set = set(df.Category)
    essential_categories = set([
        'Home Phone',
        'Tithes and Offerings',
        'Tuition',
        'Life Insurance',
        'Gas & Fuel',
        'Personal Care',
        'Veterinary',
        'Books & Supplies',
        'Groceries',
        'Utilities',
        'Mortgage & Rent',
        'Pet Food & Supplies',
        'Doctor',
        'Pets',
    ])
    categories = list(set(categories_set))
    categories.sort()
    year_months = list(set(df.YearMonth))
    year_months.sort()
    essential_labels = ['Essential', 'Non-Essential']
    df['essentials'] = df.Category.map(
        lambda category: essential_labels[0] if category in essential_categories else essential_labels[1]
    )

    # Splits out costs by all, essential vs non essential, and the sub charts
    # just for those essential/non-essential categories
    cost_df = df[df.adjusted_amount < 0]
    cost_totals = cost_df.groupby(['Category', 'YearMonth']).adjusted_amount.sum()
    cost = create_data_mapping(categories, year_months, cost_totals, positives=False)
    cost_plot = make_stacked_bar_chart(cost, year_months, categories, "Costs by category by month")
    show(cost_plot)

    essentials_breakout_totals = cost_df.groupby(['essentials', 'YearMonth']).adjusted_amount.sum()
    essentials_breakout_cost = create_data_mapping(essential_labels, year_months, essentials_breakout_totals, positives=False)
    essentials_breakout_cost_plot = make_stacked_bar_chart(essentials_breakout_cost, year_months, essential_labels, "Essential Breakout by month")
    show(essentials_breakout_cost_plot)

    essentials_df = cost_df[cost_df.essentials == essential_labels[0]]
    essentials_totals = essentials_df.groupby(['Category', 'YearMonth']).adjusted_amount.sum()
    essentials = create_data_mapping(categories, year_months, essentials_totals, positives=False)
    essentials_plot = make_stacked_bar_chart(essentials, year_months, categories, "Essential Only by month")
    show(essentials_plot)
    
    non_essentials_df = cost_df[cost_df.essentials == essential_labels[1]]
    non_essentials_totals = non_essentials_df.groupby(['Category', 'YearMonth']).adjusted_amount.sum()
    non_essentials = create_data_mapping(categories, year_months, non_essentials_totals, positives=False)
    non_essentials_plot = make_stacked_bar_chart(non_essentials, year_months, categories, "Non-Essential Only by month")
    show(non_essentials_plot)

    # Income chart
    income_df = df[df.adjusted_amount > 0]
    income_totals = income_df.groupby(['Category', 'YearMonth']).adjusted_amount.sum()
    income = create_data_mapping(categories, year_months, income_totals, positives=True)
    income_plot = make_stacked_bar_chart(income, year_months, categories, "Income by category by month")
    show(income_plot)
    return df


def create_data_mapping(categories, year_months, totals, positives=False):
    data = defaultdict(list)
    data.update({'year-months': year_months})
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
    return data


def make_stacked_bar_chart(data, year_months, categories, title):
    plot = figure(
        x_range=year_months,
        title=title,
        tools="hover",
        tooltips="$name : @$name{$0,0.00}",
    )
    plot.vbar_stack(
        categories,
        x='year-months',
        color=HEX_COLORS[0:len(categories)],
        source=data,
    )
    plot.y_range.start = 0
    plot.x_range.range_padding = 0.1
    plot.xgrid.grid_line_color = None
    plot.axis.minor_tick_line_color = None
    plot.outline_line_color = None
    return plot


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file_to_upload')
    three_months_ago = datetime.now() - timedelta(days=90)
    start_of_three_months_ago = datetime(
        three_months_ago.year,
        three_months_ago.month,
        1,
    )
    parser.add_argument(
        '--earliest_date',
        type=lambda x: datetime.fromisoformat(x),
        required=False,
        default=start_of_three_months_ago,
    )
    args = parser.parse_args()
    main(args.file_to_upload, args.earliest_date)
