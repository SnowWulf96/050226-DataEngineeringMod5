import unittest
import pandas as pd

from master_data_cleaner import (
    Check_Customer_Ids,
    Convert_to_datetime,
    calculate_days_borrowed,
    calculate_metrics,
    check_checkout_not_after_returned,
    convert_blanks,
    convert_to_int,
    convert_xweeks_to_no_days,
    drop_duplicates_and_na,
    drop_na_required_columns,
    if__date_invalid_infer_checkout,
    strip_quotes,
)


class TestMasterDataCleaner(unittest.TestCase):
    # Check that empty text is treated as missing data.
    def test_convert_blanks_replaces_empty_and_whitespace(self):
        #Create DF with empty, spaces, string
        df = pd.DataFrame({"a": ["", "   ", "text"], "b": [1, 2, 3]})
        #run test
        result = convert_blanks(df)
        ##check that first two rows in column "a" are now NA and third row is unchanged
        self.assertTrue(pd.isna(result.loc[0, "a"]))
        self.assertTrue(pd.isna(result.loc[1, "a"]))
        self.assertEqual(result.loc[2, "a"], "text")

    # Check that duplicates are removed and rows with all key fields missing are removed.
    def test_drop_duplicates_and_na_removes_duplicate_and_all_na_subset_rows(self):
        ##setup sample
        df = pd.DataFrame(
            {
                "Customer ID": [1, 1, pd.NA, 2],
                "Books": ["Book A", "Book A", pd.NA, "Book B"],
            }
        )
        ##apply test func
        result = drop_duplicates_and_na(df, ["Customer ID", "Books"])
        #check that only unique rows with non-missing Customer ID and Books remain
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result["Customer ID"].tolist()), {1, 2})

    # Check that rows missing required fields are dropped.
    def test_drop_na_required_columns_drops_rows_with_missing_required_values(self):
        ##setup sample df
        df = pd.DataFrame(
            {
                "Customer ID": [1, pd.NA, 2],
                "Books": ["Book A", "Book B", pd.NA],
            }
        )
        ##apply test func with Customer ID and Books as required columns
        result = drop_na_required_columns(df, ["Customer ID", "Books"])
        ##check that only the row with both Customer ID and Books present remains
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["Customer ID"], 1)

    # Check that only valid customer IDs remain after filtering.
    def test_check_customer_ids_filters_non_matching_customer_ids(self):
        ##setup dfs with some matching and some non-matching Customer IDs
        books_df = pd.DataFrame({"Customer ID": [1, 2, 999], "Books": ["A", "B", "C"]})
        customers_df = pd.DataFrame({"Customer ID": [1, 2]})
        ##apply test
        result = Check_Customer_Ids(books_df, customers_df)
        ##check that only rows with Customer ID 1 and 2 remain
        self.assertEqual(result["Customer ID"].tolist(), [1, 2])

    #check quotes are stripped
    def test_strip_quotes(self):
        ##sample data
        df = pd.DataFrame({"Books": ['"Book A"', """Book B""", "Book C"]})
        ##apply test
        result = strip_quotes(df, "Books")
        ##validate that quotes are removed but text is intact
        self.assertEqual(result["Books"].tolist(), ["Book A", "Book B", "Book C"])

    #check checkout dates are inferred if NA
    def test_checkout_dates_inferred_if_na(self):
        #sample data
        df = pd.DataFrame(
            {
                "Book checkout": [pd.NA],
                "Book Returned": [pd.Timestamp("2023-06-10")],
                "Days allowed to borrow": [14],
            }
        )
        #apply function
        result = if__date_invalid_infer_checkout(df)

        ##validate that checkout date is inferred as returned date minus allowed borrow days
        self.assertTrue(pd.notna(result.loc[0, "Book checkout"]))
        self.assertEqual(result.loc[0, "Book checkout"], pd.Timestamp("2023-05-27"))

    # Check that week text values are converted into day counts.
    def test_convert_xweeks_to_no_days_converts_week_strings_to_days(self):
        #sample data
        df = pd.DataFrame({"Days allowed to borrow": ["2 weeks", "3 week", 10]})
        #apply function
        result = convert_xweeks_to_no_days(df, "Days allowed to borrow")
        #validate that "2 weeks" is converted to 14, "3 week" to 21, and numeric value remains unchanged
        self.assertEqual(result["Days allowed to borrow"].tolist(), [14, 21, 10])

    # Check that impossible timelines are flagged by clearing checkout date.
    def test_check_checkout_not_after_returned_sets_invalid_checkout_to_na(self):
        #sample data with checkout date after returned date
        df = pd.DataFrame(
            {
                "Book checkout": [pd.Timestamp("2023-06-10")],
                "Book Returned": [pd.Timestamp("2023-06-01")],
            }
        )
        ##apply func    
        result = check_checkout_not_after_returned(df)
        ##validate that checkout date is set to NA due to being after returned date
        self.assertTrue(pd.isna(result.loc[0, "Book checkout"]))

    # Check that a "Days Borrowed" column is added with the correct value.
    def test_calculate_days_borrowed_adds_numeric_days_column(self):
        #sample data with valid checkout and returned dates
        df = pd.DataFrame(
            {
                "Book checkout": [pd.Timestamp("2023-06-01")],
                "Book Returned": [pd.Timestamp("2023-06-10")],
            }
        )
        result = calculate_days_borrowed(df)
    #validate column added and is correct
        self.assertIn("Days Borrowed", result.columns)
        self.assertEqual(result.loc[0, "Days Borrowed"], 9)

if __name__ == '__main__':
    unittest.main()
