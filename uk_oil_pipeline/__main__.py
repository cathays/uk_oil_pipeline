import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import logging
from pathlib import Path
import argparse

url = "https://www.gov.uk/government/statistics/oil-and-oil-products-section-3-energy-trends"
date_mapping = {"1": "/03/31",
                "2": "/06/30",
                "3": "/09/30",
                "4": "/12/31"}
date_clean = {" ": "",
              "\n": ""}
log = logging.getLogger("logger")


def getLink(url):
    """
    Function retrieves the latest link to the "Supply and use of crude oil, natural gas liquids and feedstocks
    (ET 3.1 - quarterly)" document.
    :param url: url of government page containing this document
    :return: string of the url of the document
    """
    logging.info("Obtaining XLSX URL")
    html_page = urlopen(Request(url))
    soup = BeautifulSoup(html_page, "lxml")
    links = []
    for link in soup.findAll('a'):
        links.append(link.get('href'))
    my_links = [x for x in links if "ET_3.1_" in x]
    logging.info(f"Retrieved URL {my_links[0]}")
    return my_links[0]


def checkNewLink(link):
    """
    Checks existing links used, if this is a new one then will extract. If not then the program will be terminated
    :param link: Link to the data
    """
    logging.info("Checking for new source document")

    if Path('links.txt').is_file() is False:
        open('links.txt', 'w')

    with open(r'links.txt', 'r') as file:
        read_links = file.read()

    if link not in read_links:
        with open(r'links.txt', 'a') as file:
            file.write(f"\n{link}")
    else:
        logging.warning("No new source document detected.")
        quit()


def transformDate(date_string):
    """
    Transforms the dates from the document into a datetime object
    :param date_string: date from source
    :return: datetime object
    """
    if date_string[-1:] is "1":
        date = f"{date_string[:-1]}-03-31"
    elif date_string[-1:] is "2":
        date = f"{date_string[:-1]}-06-30"
    elif date_string[-1:] is "3":
        date = f"{date_string[:-1]}-09-30"
    elif date_string[-1:] is "4":
        date = f"{date_string[:-1]}-12-31"
    else:
        logging.error(f"Error converting dates to datetime object. Errored date is {date_string}")
        raise ValueError("Error converting dates")
    date = pd.to_datetime(date)
    return date


def pullData(link):
    """
    Pulls data from source
    :param link: link to source data
    :return: dataframe containing source data
    """
    logging.info("Reading source data")
    df = pd.read_excel(link,
                       sheet_name='Quarter',
                       skiprows=range(1, 4),
                       index_col=0)
    df = df.transpose()
    df.reset_index(inplace=True)
    df.drop("index", axis=1, inplace=True)
    return df


def correctDates(df):
    """
    Turns the strings from the source data into dates e.g. 1999 1st Quarter = 1999/03/30
    :param df: dataframe containing source data
    :return: dataframe with formatted dates
    """
    logging.info("Converting date format")
    df.rename(columns={'Column1': 'date'}, inplace=True)
    df['date'] = df['date'].replace(date_clean, regex=True)
    df['date'] = df['date'].str[0:5]
    df['date'] = df.apply(lambda row: transformDate(row['date']), axis=1)
    return df


def getFileName(link):
    """
    Retrieves original file name from the URL
    :param link: url of original data
    :return: string of original file name
    """
    logging.info("Getting file name")
    file_name = link.rsplit('/', 1)[1]
    file_name = file_name.rsplit('.', 1)[0]
    return file_name


def correctColNames(df):
    """
    Takes column names and adds a prefix, to avoid duplicate column names.
    :param df: Dataframe of data from source
    :return: Dataframe with unique column names
    """
    logging.info("Adjusting column names")
    cols = df.columns
    cols_df = pd.DataFrame(cols)
    cols_df2 = cols_df.copy()
    cols_df = pd.concat([cols_df, cols_df2], axis=1)
    cols_df.columns = ['Prefix', 'name']
    cols_df['Prefix'] = cols_df['Prefix'].where(cols_df['Prefix'].astype(str).str.contains('\[.*\]'), None)
    cols_df = cols_df.ffill()
    cols_df.fillna('date', inplace=True)
    cols_df['col3'] = cols_df['Prefix'].where(cols_df['Prefix'].eq(cols_df['name']),
                                              cols_df['Prefix'] + ' - ' + cols_df['name'])
    col_list = cols_df['col3'].tolist()
    df.columns = col_list
    return df


def checkColsVSPrev(df):
    """
    Checks current column names vs previous column names. Raises error if there are differences
    :param df: Dataframe containing data
    """
    logging.info("Comparing column names")
    last_df = pd.read_csv('Latest_Version.csv')
    last_cols = last_df.columns
    current_cols = df.columns
    different_cols = list(last_cols.difference(current_cols))
    if len(different_cols) > 0:
        logging.error(f"{len(different_cols)} differences found in between previous and current column names")
        raise ValueError("Columns different to previous")


def compileProfilingReport(df):
    """
    Compiles profiling report on the data
    :param df: Dataframe containing the data
    :return: Dataframe containing profiling information
    """
    logging.info("Compiling Profile Report")
    profile_df = pd.DataFrame(columns=['field', 'max', 'min', 'mean', 'median'])
    for column in df:
        max = df[column].max()
        min = df[column].min()
        mean = df[column].mean()
        median = df[column].median()
        row = [column, max, min, mean, median]
        profile_df = profile_df.append(
            {'field': row[0], 'max': row[1], 'min': row[2], 'mean': row[3], 'median': row[4]},
            ignore_index=True)

    profile_df = profile_df[profile_df.field != 'date']
    profile_df = profile_df.append({'field': 'Row Count', 'max': df.shape[0]}, ignore_index=True)
    profile_df = profile_df.append({'field': 'Column Count', 'max': df.shape[1]}, ignore_index=True)
    profile_df = profile_df.append({'field': 'Null Count', 'max': df.isnull().sum().sum()}, ignore_index=True)
    return profile_df


def main():
    """
    Main function to run the pipeline
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    target = Path(args.path)
    link = getLink(url)
    filename = getFileName(link)
    # checkNewLink(link)
    df = pullData(link)
    df = correctDates(df)
    df = correctColNames(df)
    df.to_csv('Latest_Version.csv', index=False)
    checkColsVSPrev(df)
    profiling_df = compileProfilingReport(df)
    # Need to adjust the below to take a command line arg
    profiling_df.to_csv(fr'{target}\{filename}_data_profiling.csv')
    df.to_csv(fr'{target}\{filename}.csv')
    logging.info("Complete!")


if __name__ == '__main__':
    main()
