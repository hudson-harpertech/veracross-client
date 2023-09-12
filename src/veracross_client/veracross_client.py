import requests
import pandas as pd
import json
import http.client

# available_scopes = {
#     'academics.assignments.grades:list': 'Read assignment grades data',
#     'academics.students:list': 'Read list of students',
#     'classes:list': 'Read list of classes',
#     # Add more scopes and their descriptions as needed
# }


class VeracrossClient:
    def __init__(self, school_route, client_id, client_secret, scopes):
        """
        Initialize the Veracross API client.

        Parameters:
            school_route (str): The school route used to construct the base URL. It should be in the format used in the API, e.g., 'school_name' or 'school_name/testing'.
            client_id (str): The client ID used for authentication.
            client_secret (str): The client secret used for authentication.
            scopes (list): A list of scopes for the API access. It should consist of the available scopes listed in the `available_scopes` variable.
        """

        self.school_route = school_route
        self.base_url = f"https://api.veracross.com/{school_route}/v3"
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes

        conn = http.client.HTTPSConnection("accounts.veracross.com")
        payload = f"grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}&scope={' '.join(self.scopes)}"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}
        conn.request("POST", f"/{school_route}/oauth/token", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        try:
            self.access_token = data['access_token']
        except KeyError:
            print(f"Error: {data['error_description']}")

    def fetch_data_from_api(self, endpoint, headers, params):
        """
        Helper function to fetch data from an API endpoint using the GET method with pagination support.

        Parameters:
            endpoint (str): The specific API endpoint to fetch data from.
            headers (dict): Headers required for API authentication and pagination.
            params (dict): Query parameters for filtering the data.

        Returns:
            list: A list containing the fetched data from all pages.
        """

        headers['Authorization'] = f"Bearer {self.access_token}"

        data = []
        while True:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=headers, params=params)
            if response.status_code == 200:
                chunk_data = response.json().get('data', [])
                data.extend(chunk_data)

                if chunk_data == []:
                    break

                headers['X-Page-Number'] = str(
                    int(headers['X-Page-Number']) + 1)
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break

        return data

    def expand_dict_columns(self, df, columns_to_expand):
        """
        Expand DataFrame columns containing dictionaries into multiple columns.

        Parameters:
            df (pandas.DataFrame): The DataFrame containing the columns with dictionaries.
            columns_to_expand (list): A list of column names containing the dictionaries.

        Returns:
            pandas.DataFrame: A new DataFrame with the expanded columns.
        """
        # Create a list to collect the rows of the expanded DataFrame
        expanded_rows = []

        # Iterate over the rows of the original DataFrame
        for _, row in df.iterrows():
            values_to_add = {}
            for column in columns_to_expand:
                dictionary = row[column]
                if dictionary is not None:
                    for key, value in dictionary.items():
                        new_col_name = f"{column}_{key}"
                        values_to_add[new_col_name] = value
            expanded_rows.append(values_to_add)

        # Create the expanded DataFrame from the list of rows
        expanded_df = pd.DataFrame(expanded_rows)

        # Drop the original columns and concatenate the expanded DataFrame
        df = pd.concat(
            [df.drop(columns_to_expand, axis=1), expanded_df], axis=1)

        return df

    def get_assignment_grades(self, assignment_id, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, student_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of assignment grades for a specific assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            last_modified_date (str, optional): Only return grades that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return grades that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return grades that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            student_id (int, optional): Only return grades for the specified student ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of assignment grades.

        """
        if 'Academics: Assignment Grades:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Academics: Assignment Grades:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/assignment_grades/{assignment_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'student_id': student_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_assignment_grades(self, assignment_id, id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the assignment grades.

        Args:
            assignment_id (int): The ID of the assignment.
            id (int): The ID of the grade.

        Returns:
            pandas.DataFrame: A DataFrame containing the assignment grades.

        """
        if 'academics.assignments.grades:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.assignments.grades:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/assignments/{assignment_id}/grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_assignment_grades(self, assignment_id, id, data, completion_status, raw_score, private_notes_for_teacher, last_modified_date, x_api_revision):
        """
        Update the grades for an assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            id (int): The ID of the grade.
            data (object): The data object containing the updated grade information.
            completion_status (int): The completion status of the assignment.
            raw_score (float): The raw score for the assignment.
            private_notes_for_teacher (str): The private notes for the teacher.
            last_modified_date (str): The last modified date of the grade.
            x_api_revision (str): The X-API-Revision header value.

        Returns:
            None.
        """
        if 'update_assignment_grades' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'update_assignment_grades' to your scopes.")
            return

        endpoint = f"assignments/{assignment_id}/grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        params = {}

        body_data = {
            'data': data,
            'completion_status': completion_status,
            'raw_score': raw_score,
            'private_notes_for_teacher': private_notes_for_teacher,
            'last_modified_date': last_modified_date
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, params, body_data)
            if response.status_code == 204:
                print("Grades successfully updated.")
            else:
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error: {str(e)}")

    def get_academics_block_groups(self, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of academic block groups.

        Args:
            x_api_revision (str, optional): API revision.
            x_api_value_lists (str, optional): Include Value Lists in response.
            x_page_number (int, optional): Page number.
            x_page_size (int, optional): Number of records per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic block groups.
        """
        if 'academics.config.block_groups:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.block_groups:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/config/block_groups"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_block_groups(self, id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the details of an academic block group.

        Args:
            id (int): The ID of the academic block group.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): The value lists for the API.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the academic block group.
        """
        if 'academics.block_groups:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.block_groups:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/block_groups/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_config_blocks_by_group(self, block_group_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of academic config blocks by block groups.

        Args:
            block_group_id (int): The ID of the block group.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic config blocks by block groups.

        """
        if 'academics.config.blocks_by_block_groups:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.blocks_by_block_groups:list' to your scopes.")
            return pd.DataFrame()

        endpoint = 'academics/config/blocks_by_block_groups'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'block_group_id': block_group_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_blocks_by_group(self, id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic blocks by group.

        Args:
            id (int, required): The ID of the block group.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic blocks by group.
        """
        if 'academics.blocks_by_group:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.blocks_by_group:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/block_groups/{id}/blocks"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_calendar_rotation_days(self, block_schedule_id=None, date=None, date_on_or_after=None, date_on_or_before=None, day_id=None, rotation_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of calendar rotation days for academics.

        Args:
            block_schedule_id (int, optional): Only return calendar rotation days for the specified block schedule ID.
            date (str, optional): Only return calendar rotation days for the specified date.
            date_on_or_after (str, optional): Only return calendar rotation days on or after the specified date.
            date_on_or_before (str, optional): Only return calendar rotation days on or before the specified date.
            day_id (int, optional): Only return calendar rotation days for the specified day ID.
            rotation_id (int, optional): Only return calendar rotation days for the specified rotation ID.
            school_year (int, optional): Only return calendar rotation days for the specified school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of calendar rotation days.

        """
        if 'academics.calendar_rotation_days:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.calendar_rotation_days:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/calendar_rotation_days"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'block_schedule_id': block_schedule_id,
            'date': date,
            'date_on_or_after': date_on_or_after,
            'date_on_or_before': date_on_or_before,
            'day_id': day_id,
            'rotation_id': rotation_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_calendar_rotation_day(self, id, school_year, date, rotation, x_api_revision=None, x_api_value_lists=None):
        """
        Get the calendar rotation day with the specified ID.

        Args:
            id (int): The ID of the calendar day rotation.
            school_year (int): The school year of the calendar day rotation.
            date (str): The date of the calendar day rotation. Format: "YYYY-MM-DD".
            rotation (dict): The rotation details for the calendar day rotation.
            x_api_revision (str, optional): API revision header.
            x_api_value_lists (str, optional): Include value lists in the response header.

        Returns:
            pandas.DataFrame: A DataFrame containing the calendar rotation day details.
        """
        if 'Academics: Calendar Rotation Days' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Academics: Calendar Rotation Days' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/calendar_rotation_day/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_class_assignments(self, internal_class_id=None, assignment_type=None, description=None, assignment_details=None, max_score=None, weight=None, not_to_be_graded=None, date_assigned=None, date_due=None, display_status=None):
        """
        Create class assignments.

        Args:
            internal_class_id (int, required): The ID of the internal class.
            assignment_type (int, required): The type of the assignment.
            description (str, required): The description of the assignment.
            assignment_details (str, required): The details of the assignment.
            max_score (int, required): The maximum score of the assignment.
            weight (int, required): The weight of the assignment.
            not_to_be_graded (bool, required): Boolean indicating if the assignment should not be graded.
            date_assigned (str, required): The date when the assignment was assigned. Format: "YYYY-MM-DD".
            date_due (str, required): The due date of the assignment. Format: "YYYY-MM-DD".
            display_status (int, required): The display status of the assignment.

        Returns:
            pandas.DataFrame: A DataFrame containing the created class assignments.

        """
        if 'academics.classes.assignments:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.classes.assignments:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/assignments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }
        data = {
            'internal_class_id': internal_class_id,
            'assignment_type': assignment_type,
            'description': description,
            'assignment_details': assignment_details,
            'max_score': max_score,
            'weight': weight,
            'not_to_be_graded': not_to_be_graded,
            'date_assigned': date_assigned,
            'date_due': date_due,
            'display_status': display_status
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_class_assignments(self, internal_class_id, assignment_type=None, date_assigned=None, date_due=None, last_modified_date=None, on_or_after_date_assigned=None, on_or_after_date_due=None, on_or_after_last_modified_date=None, on_or_before_date_assigned=None, on_or_before_date_due=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of assignments for a specific academic class.

        Args:
            internal_class_id (int): The ID of the academic class.
            assignment_type (int, optional): The type of the assignment.
            date_assigned (str, optional): Only return assignments assigned on this specific date. Format: "YYYY-MM-DD".
            date_due (str, optional): Only return assignments due on this specific date. Format: "YYYY-MM-DD".
            last_modified_date (str, optional): Only return assignments that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_date_assigned (str, optional): Only return assignments assigned on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_date_due (str, optional): Only return assignments due on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return assignments that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_date_assigned (str, optional): Only return assignments assigned on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_date_due (str, optional): Only return assignments due on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return assignments that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number for pagination. Default is 1.
            x_page_size (int, optional): The page size for pagination. Default is 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of assignments for the academic class.

        """
        if 'academics.class_assignments:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.class_assignments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/assignments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'assignment_type': assignment_type,
            'date_assigned': date_assigned,
            'date_due': date_due,
            'last_modified_date': last_modified_date,
            'on_or_after_date_assigned': on_or_after_date_assigned,
            'on_or_after_date_due': on_or_after_date_due,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_date_assigned': on_or_before_date_assigned,
            'on_or_before_date_due': on_or_before_date_due,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def delete_academics_class_assignment(self, id: int, internal_class_id: int, x_api_revision: str = None):
        """
        Delete an academic class assignment.

        Args:
            id (int): The ID of the class assignment to be deleted.
            internal_class_id (int): The internal ID of the class to which the assignment belongs.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: An empty DataFrame.

        """
        if 'academics.classes.assignments:delete' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes.assignments:delete' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/assignments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint}", headers=headers)
            if response.status_code == 200:
                print(
                    f"The class assignment with ID {id} was successfully deleted.")
            else:
                print(f"Error: {response.status_code} - {response.text}")

            return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_class_assignments(self, internal_class_id=None, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the list of class assignments for a specific academic class.

        Args:
            internal_class_id (int, required): The internal ID of the academic class.
            id (int, optional): The ID of the class assignment.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of class assignments.

        """
        if 'Academics: Class Assignments' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Academics: Class Assignments' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/assignments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {
            'id': id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_class_assignment(self, internal_class_id, id, data):
        """
        Update an academic class assignment.

        Args:
            internal_class_id (int): The internal ID of the class.
            id (int): The ID of the assignment.
            data (dict): The updated assignment data. It should contain the following fields:
                - assignment_type (int): The type of the assignment.
                - description (str): The description of the assignment.
                - assignment_details (str): The details of the assignment.
                - max_score (int): The maximum score of the assignment.
                - weight (int): The weight of the assignment.
                - not_to_be_graded (bool): Whether the assignment should not be graded.
                - date_assigned (str): The date the assignment is assigned. Format: "YYYY-MM-DD".
                - date_due (str): The due date of the assignment. Format: "YYYY-MM-DD".
                - display_status (int): The display status of the assignment.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated assignment.
        """
        if 'academics.classes.assignments:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.classes.assignments:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/assignments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': "string"
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)

            if response.get('status') == 'error':
                print(f"Error: {response.get('message', '')}")
                return pd.DataFrame()

            df = pd.DataFrame(response.get('data', []))

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_class_meeting_times(self, internal_class_id, date=None, grading_period_id=None, on_or_after_date=None, on_or_before_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        List the meeting times for a specific academic class.

        Args:
            internal_class_id (int): The internal ID of the class.

            date (str, optional): The calendar date for filtering the meeting times.

            grading_period_id (int, optional): The ID of the grading period for filtering the meeting times.

            on_or_after_date (str, optional): Return meeting times on or after this specific date.

            on_or_before_date (str, optional): Return meeting times on or before this specific date.

            x_api_revision (str, optional): The API revision for the request.

            x_api_value_lists (str, optional): Include value lists in the response. Allowed value: "include".

            x_page_number (int, optional): The page number for pagination. Must be greater than or equal to 1. Default: 1.

            x_page_size (int, optional): The number of records per page for pagination. Must be between 1 and 1000. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the meeting times for the academic class.

        """
        if 'academics.classmeetingtimes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classmeetingtimes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/meeting_times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'date': date,
            'grading_period_id': grading_period_id,
            'on_or_after_date': on_or_after_date,
            'on_or_before_date': on_or_before_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_class_meeting_times(self, internal_class_id=None, id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of meeting times for a specific academic class.

        Args:
            internal_class_id (int, optional): The internal ID of the academic class.
            id (int, optional): The ID of the meeting time.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of meeting times for the academic class.

        """
        if 'academics.classes.meeting_times:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes.meeting_times:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{internal_class_id}/meeting_times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'id': id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_classes(self, course_type=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, primary_teacher_id=None, room_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic classes.

        Args:
            course_type (str, optional): The type of the course.
            on_or_after_last_modified_date (str, optional): Only return classes that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return classes that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            primary_teacher_id (int, optional): Only return classes taught by the specified primary teacher ID.
            room_id (int, optional): Only return classes taught in the specified room ID.
            school_year (int, optional): Only return classes from the specified school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic classes.

        """
        if 'academics.classes:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'course_type': course_type,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_classes(self, class_id, description, status, school_year, begin_date, end_date, primary_grade_level_id, school_level, internal_course_id, primary_teacher_id, room_id, virtual_meeting_url, subject_id, x_api_revision=None):
        """
        Create an academic class.

        Args:
            class_id (str): The ID of the class.
            description (str): The description of the class.
            status (int): The status of the class.
            school_year (int): The school year of the class.
            begin_date (str): The begin date of the class. Format: "YYYY-MM-DD".
            end_date (str): The end date of the class. Format: "YYYY-MM-DD".
            primary_grade_level_id (int): The ID of the primary grade level.
            school_level (int): The ID of the school level.
            internal_course_id (int): The ID of the course.
            primary_teacher_id (int): The ID of the primary teacher.
            room_id (int): The ID of the room.
            virtual_meeting_url (str): The virtual meeting URL of the class.
            subject_id (int): The ID of the subject.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the created academic class.

        """
        if 'academics.classes:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'class_id': class_id,
            'description': description,
            'status': status,
            'school_year': school_year,
            'begin_date': begin_date,
            'end_date': end_date,
            'primary_grade_level_id': primary_grade_level_id,
            'school_level': school_level,
            'internal_course_id': internal_course_id,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'virtual_meeting_url': virtual_meeting_url,
            'subject_id': subject_id
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_classes(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of an academic class.

        Args:
            id (int): The ID of the academic class.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the academic class.

        """
        if 'academics.classes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_classes(self, id, data, x_api_revision=None):
        """
        Update an academic class.

        Args:
            id (str): The ID of the class to be updated.
            data (dict): The updated data for the class.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated class.

        """
        if 'academics.classes:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                updated_class = response.json().get('data', {})
                df = pd.DataFrame(updated_class)
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_permissions(self, class_id=None, course_id=None, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, person_id=None, school_level=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of academic permissions.

        Args:
            class_id (int, optional): The ID of the class.
            course_id (int, optional): The ID of the course.
            last_modified_date (str, optional): Only return permissions that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return permissions that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return permissions that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): Only return permissions for the specified person ID.
            school_level (int, optional): Only return permissions for the specified school level.
            school_year (int, optional): Only return permissions for the specified school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic permissions.

        """
        if 'academics.permissions:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.permissions:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/permissions"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'class_id': class_id,
            'course_id': course_id,
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id,
            'school_level': school_level,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_class_permissions(self, id):
        """
        Get the class permissions for a specific ID.

        Args:
            id (int): The ID of the class permission.

        Returns:
            pandas.DataFrame: A DataFrame containing the class permission data.
        """
        if 'academics.permissions:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.permissions:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/permissions/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_configuration_block_times(self, block_id=None, block_schedule_id=None, rotation_day_id=None, rotation_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic configuration block times.

        Args:
            block_id (int, optional): Only return block times for the specified block ID.
            block_schedule_id (int, optional): Only return block times for the specified block schedule ID.
            rotation_day_id (int, optional): Only return block times for the specified rotation day ID.
            rotation_id (int, optional): Only return block times for the specified rotation ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic configuration block times.

        """
        if 'academics.configuration.block_times:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.configuration.block_times:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/configuration/block_times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'block_id': block_id,
            'block_schedule_id': block_schedule_id,
            'rotation_day_id': rotation_day_id,
            'rotation_id': rotation_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_configuration_block_times(self, id=None, x_api_revision=None, x_api_value_lists=None, data=None):
        """
        Get the configuration of block times for academics.

        Args:
            id (int, required): Period Time ID.
            x_api_revision (str): API Revision.
            x_api_value_lists (str): Include Value Lists in response.

        Returns:
            pandas.DataFrame: A DataFrame containing the configuration of block times for academics.

        """
        if 'academics.config.block_times:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.block_times:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/config/block_times/{id}"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params=data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_configuration_block_schedules(self, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic configuration block schedules.

        Args:
            x_api_revision (str, optional): The API revision version.
            x_api_value_lists (str, optional): Include value lists in the response.
            x_page_number (int, optional): The page number of the response.
            x_page_size (int, optional): The number of entries per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic configuration block schedules.

        """
        if 'academics.configuration_block_schedules:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.configuration_block_schedules:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/configuration_block_schedules"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_block_schedule(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the block schedule by ID.

        Args:
            id (int): The ID of the block schedule.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response. Allowed value: include.

        Returns:
            pandas.DataFrame: A DataFrame containing the block schedule.

        """
        if 'academics.config.block_schedules:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.block_schedules:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/config/block_schedules/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params={})
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_configuration_blocks_periods(self, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of configuration blocks periods.

        Args:
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number.
            x_page_size (int, optional): The page size.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of configuration blocks periods.
        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/config/blocks"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_config_blocks(self, id, x_page_number=1, x_page_size=1000):
        """
        Get the specified academic configuration block.

        Args:
            id (int): The ID of the academic configuration block.

        Returns:
            pandas.DataFrame: A DataFrame containing the specified academic configuration block.

        """
        if 'academics.config.blocks:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.config.blocks:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/config/blocks/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_course(self, course_id, name, subject_id, catalog_title, catalog_description, course_type, x_api_revision=None):
        """
        Create a new academic course.

        Args:
            course_id (str): The ID of the course.
            name (str): The name of the course.
            subject_id (str): The ID of the subject.
            catalog_title (str): The title of the course in the catalog.
            catalog_description (str): The description of the course in the catalog.
            course_type (int): The type of the course.

        Returns:
            pandas.DataFrame: A DataFrame containing the newly created academic course.
        """
        if 'academics.courses:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.courses:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/courses/"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'course_id': course_id,
            'name': name,
            'subject_id': subject_id,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description,
            'course_type': course_type
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers=headers, data=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_courses(self, classification=None, course_type=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, subject_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of academic courses.

        Args:
            classification (int, optional): The classification of the course.
            course_type (int, optional): The type of the academic course.
            on_or_after_last_modified_date (str, optional): Only return courses that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return courses that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            subject_id (int, optional): Only return courses with the specified subject ID.
            x_api_revision (str, optional): API revision.
            x_api_value_lists (str, optional): Include value lists in the response. Allowed values: "include".
            x_page_number (int, optional): Page number. Default: 1.
            x_page_size (int, optional): Number of records per page. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic courses.
        """
        if 'academics.courses:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.courses:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'classification': classification,
            'course_type': course_type,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'subject_id': subject_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_courses(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get information about an academic course.

        Args:
            id (int): The ID of the academic course.

        Returns:
            pandas.DataFrame: A DataFrame containing the information about the academic course.
        """
        if 'academics.courses:get' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.courses:get' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_courses(self, id, data, x_api_revision=None):
        """
        Update an academic course.

        Args:
            id (int): The internal Course ID.
            data (dict): The updated course data. It should include the following keys:
                - course_id (str): The course ID.
                - name (str): The name of the course.
                - subject_id (int): The ID of the subject.
                - subject_description (str): The description of the subject.
                - department_description (str): The description of the department.
                - catalog_title (str): The title of the course catalog.
                - catalog_description (str): The description of the course catalog.
                - classification (int): The classification of the course.
                - course_type (int): The type of the course.
            x_api_revision (str, optional): The API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated course data.

        """
        if 'academics.courses:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.courses:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.send_patch_request(endpoint, headers, data)
            if response.status_code == 200:
                course_data = response.json().get('data', {})
                df = pd.DataFrame(course_data)
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_departments(self, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic departments.

        Args:
            last_modified_date (str, optional): Only return departments that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return departments that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return departments that were last modified on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic departments.

        """
        if 'academics.departments:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.departments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/departments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academic_department(self, id):
        """
        Get the details of an academic department.

        Args:
            id (int): The ID of the academic department.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the academic department.
        """
        if 'academics.departments:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.departments:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/departments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_enrollments(self, course_type=None, internal_class_id=None, person_id=None, school_year=None, subject=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic enrollments.

        Args:
            course_type (str, optional): The type of the course.
            internal_class_id (int, optional): The internal ID of the class.
            person_id (int, optional): The ID of the person.
            school_year (int, optional): The school year.
            subject (str, optional): The subject of the course.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic enrollments.

        """
        if 'academics.enrollments:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.enrollments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'course_type': course_type,
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'school_year': school_year,
            'subject': subject
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_enrollment(self, id):
        """
        Get enrollment details for a specific enrollment ID.

        Args:
            id (int): The ID of the enrollment.

        Returns:
            pandas.DataFrame: A DataFrame containing the enrollment details.
        """
        if 'academics.enrollments:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.enrollments:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/enrollments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string',
            'X-API-Value-Lists': 'string'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params={})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_enrollment(self, id, data):
        """
        Update the enrollment for a student in an academic class.

        Args:
            id (int): The ID of the enrollment to be updated.
            data (dict): A dictionary containing the updated enrollment data.
                - currently_enrolled (bool): Whether the student is currently enrolled in the class.
                - late_date_enrolled (str): The date when the student was enrolled in the class (format: "YYYY-MM-DD").
                - date_withdrawn (str): The date when the student withdrew from the class (format: "YYYY-MM-DD").
                - level (int): The level of the student in the class.
                - notes (str): Any additional notes or comments.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated enrollment details.

        """

        if 'academics.enrollment:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.enrollment:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/enrollment/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.patch_data_to_api(endpoint, headers, data)
            df = pd.DataFrame([response])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_enrollments(self, internal_class_id, person_id, currently_enrolled, late_date_enrolled, date_withdrawn, level, notes, x_api_revision):
        """
        Create a new enrollment record for an academic class.

        Args:
            internal_class_id (int): The ID of the internal class.
            person_id (int): The ID of the person.
            currently_enrolled (bool): Indicates if the person is currently enrolled.
            late_date_enrolled (str): The late date enrolled. Format: "YYYY-MM-DD".
            date_withdrawn (str): The date withdrawn. Format: "YYYY-MM-DD".
            level (int): The enrollment level.
            notes (str): Additional notes for the enrollment.
            x_api_revision (str): API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the newly created enrollment record.
        """
        if 'academics.enrollments:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.enrollments:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'currently_enrolled': currently_enrolled,
            'late_date_enrolled': late_date_enrolled,
            'date_withdrawn': date_withdrawn,
            'level': level,
            'notes': notes
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_grading_periods(self, group_id=None, last_modified_date=None, on_or_after_end_date=None, on_or_after_last_modified_date=None, on_or_after_start_date=None, on_or_before_end_date=None, on_or_before_last_modified_date=None, on_or_before_start_date=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of grading periods.

        Args:
            group_id (int, optional): The ID of the group.
            last_modified_date (str, optional): Only return grading periods that were last modified on the specified date. Format: "YYYY-MM-DD".
            on_or_after_end_date (str, optional): Only return grading periods that end on or after the specified date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return grading periods that were last modified on or after the specified date. Format: "YYYY-MM-DD".
            on_or_after_start_date (str, optional): Only return grading periods that start on or after the specified date. Format: "YYYY-MM-DD".
            on_or_before_end_date (str, optional): Only return grading periods that end on or before the specified date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return grading periods that were last modified on or before the specified date. Format: "YYYY-MM-DD".
            on_or_before_start_date (str, optional): Only return grading periods that start on or before the specified date. Format: "YYYY-MM-DD".
            school_year (int, optional): Only return grading periods from the specified school year.
            x_api_revision (str, optional): The API revision version.
            x_api_value_lists (str, optional): The value lists required for the API.
            x_page_number (int, optional): The page number of the results.
            x_page_size (int, optional): The maximum number of items per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of grading periods.
        """
        if 'academics.config.grading_periods:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.grading_periods:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/config/grading_periods"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'group_id': group_id,
            'last_modified_date': last_modified_date,
            'on_or_after_end_date': on_or_after_end_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_after_start_date': on_or_after_start_date,
            'on_or_before_end_date': on_or_before_end_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'on_or_before_start_date': on_or_before_start_date,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_grading_periods(self, id):
        """
        Get the details of an academic grading period.

        Args:
            id (int): The ID of the academic grading period.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the academic grading period.
        """
        if 'academics.config.grading_periods:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.config.grading_periods:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/config/grading_periods/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None,
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, None)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_numeric_grades(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of an academic numeric grade.

        Args:
            id (int): The ID of the numeric grade.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the academic numeric grade.
        """
        if 'Academics: Numeric Grades' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Academics: Numeric Grades' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/numeric_grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_numeric_grade(self, id, data, x_api_revision=None):
        """
        Update a numeric grade.

        Args:
            id (int): The ID of the grade to be updated.
            data (dict): The data to be updated for the grade.
            x_api_revision (str, optional): The API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated grade data.
        """
        if 'academics.numeric_grades:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.numeric_grades:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/numeric_grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_numeric_grades(self, class_id=None, enrollment_id=None, grading_period_id=None, last_modified_date=None, locked=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of numeric grades for academics.

        Args:
            class_id (int, optional): Internal ID of the class.
            enrollment_id (int, optional): ID of the enrollment.
            grading_period_id (int, optional): ID of the grading period.
            last_modified_date (str, optional): Last modified date. Format: "YYYY-MM-DD".
            locked (bool, optional): Indicates if the grades are locked.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of numeric grades for academics.

        """
        if 'Numeric Grades' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Numeric Grades' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/numeric-grades"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'class_id': class_id,
            'enrollment_id': enrollment_id,
            'grading_period_id': grading_period_id,
            'last_modified_date': last_modified_date,
            'locked': locked
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_qualitative_grades(self, id, enrollment_id, grading_period, student, rubric, rubric_category, rubric_criteria, proficiency_level, comment, locked, x_api_revision=None, x_api_value_lists=None):
        """
        Get the qualitative grades for a specific enrollment.

        Args:
            id (int): The ID of the grade.
            enrollment_id (int): The ID of the enrollment.
            grading_period (dict): The grading period information.
            student (dict): The student information.
            rubric (dict): The rubric information.
            rubric_category (dict): The rubric category information.
            rubric_criteria (dict): The rubric criteria information.
            proficiency_level (str): The proficiency level.
            comment (str): The comments for the grade.
            locked (bool): Flag indicating if the grade is locked.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the qualitative grades.

        """
        if 'academics.qualitative_grades:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.qualitative_grades:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/qualitative_grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_qualitative_grades(self, class_id=None, enrollment_id=None, grading_period_id=None, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, rubric_category_id=None, rubric_criteria_id=None, rubric_id=None, school_year=None, student_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of qualitative grades.

        Args:
            class_id (int, optional): Internal Class ID.
            enrollment_id (int, optional): Enrollment ID.
            grading_period_id (int, optional): ID.
            last_modified_date (str, optional): Last Modified Date.
            on_or_after_last_modified_date (str, optional): Last Modified Date.
            on_or_before_last_modified_date (str, optional): Last Modified Date.
            rubric_category_id (int, optional): ID.
            rubric_criteria_id (int, optional): Rubric Criteria ID.
            rubric_id (int, optional): ID.
            school_year (int, optional): School Year.
            student_id (int, optional): Person ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of qualitative grades.

        """
        if 'academics.qualitative_grades:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.qualitative_grades:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/qualitative_grades"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'class_id': class_id,
            'enrollment_id': enrollment_id,
            'grading_period_id': grading_period_id,
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'rubric_category_id': rubric_category_id,
            'rubric_criteria_id': rubric_criteria_id,
            'rubric_id': rubric_id,
            'school_year': school_year,
            'student_id': student_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rooms(self, building_id=None, campus_id=None, include_in_scheduler=None, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, resource_type=None, school_level_id=None, subject_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of academics rooms.

        Args:
            building_id (int, optional): The ID of the building.
            campus_id (int, optional): The ID of the campus.
            include_in_scheduler (bool, optional): Include rooms in scheduler.
            last_modified_date (str, optional): The last modified date.
            on_or_after_last_modified_date (str, optional): Only return rooms that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return rooms that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            resource_type (int, optional): The resource type.
            school_level_id (int, optional): The ID of the school level.
            subject_id (int, optional): The ID of the subject.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response.
            x_page_number (int, optional): The page number. Default: 1.
            x_page_size (int, optional): The number of records per page. Minimum: 1, Maximum: 1000. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academics rooms.

        """
        if 'academics.rooms:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rooms:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rooms"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'building_id': building_id,
            'campus_id': campus_id,
            'include_in_scheduler': include_in_scheduler,
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'resource_type': resource_type,
            'school_level_id': school_level_id,
            'subject_id': subject_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rooms(self, id):
        """
        Get a specific academic room.

        Args:
            id (int): The ID of the academic room.

        Returns:
            pandas.DataFrame: A DataFrame containing the specific academic room.
        """
        if 'academics.rooms:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rooms:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rooms/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rotation_days(self, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, rotation_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic rotation days.

        Args:
            last_modified_date (str, optional): Only return rotation days that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return rotation days that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return rotation days that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            rotation_id (int, optional): Only return rotation days for the specified rotation ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic rotation days.

        """
        if 'academics.rotation_days:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rotation_days:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rotation_days"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'rotation_id': rotation_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_config_rotation_days(self, id):
        """
        Get a specific rotation day configuration.

        Args:
            id (int): The ID of the rotation day configuration.

        Returns:
            pandas.DataFrame: A DataFrame containing the specific rotation day configuration.
        """
        if 'academics.config.rotation_days:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.config.rotation_days:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"config/rotation_days/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': '',
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_rubric_categories(self, school_route, x_api_revision, data):
        """
        Create a new academic rubric category.

        Args:
            school_route (str): The specific school route for creating the rubric category.
            x_api_revision (str): The API revision.
            data (dict): The data for creating the rubric category.
                - description (str, required): The rubric category description.
                - report_override_description (str, required): The report card description.
                - allow_curriculum (bool, required): Specify whether the rubric category allows curriculum.
                - sort_key (int, required): The sort key for ordering the rubric categories.

        Returns:
            pandas.DataFrame: A DataFrame containing the response data for the created rubric category.

        """

        if 'academics.rubric_categories:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_categories:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_categories/{school_route}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubric_categories(self, archived=False, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic rubric categories.

        Args:
            archived (bool, optional): Filter rubric categories by archived status.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic rubric categories.

        """
        if 'academics.rubric_categories:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_categories:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_categories"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'archived': archived
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_rubric_category(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the rubric category with the specified ID.

        Args:
            id (int): The ID of the rubric category.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the rubric category details.

        """
        if 'Academics: Rubric Categories' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Academics: Rubric Categories' to your scopes.")
            return pd.DataFrame()

        endpoint = f"rubric_category/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_rubric_category(self, id, data, x_api_revision=None):
        """
        Update a rubric category.

        Args:
            id (str): The ID of the rubric category to update.
            data (dict): The data to update the rubric category.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated rubric category.

        """
        if 'academics.rubric_categories:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_categories:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_categories/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            self.update_data_from_api(endpoint, headers, data)
            response_data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame([response_data])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_data_from_api(self, endpoint, headers, data):
        """
        Helper function to update data in an API endpoint using the PATCH method.

        Parameters:
            endpoint (str): The specific API endpoint to update data in.
            headers (dict): Headers required for API authentication.
            data (dict): The data to update in the API endpoint.

        Returns:
            None
        """

        headers['Authorization'] = f"Bearer {self.access_token}"
        response = requests.patch(
            f"{self.base_url}/{endpoint}", headers=headers, json=data)

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")

    def create_academics_rubric_criteria(self, data: object, category_id: int, rubric_id: int, description: str, report_override_description: str, scale_id: int, type: int, notes: str, sort_key: int):
        """
        Create a new rubric criteria.

        Args:
            data (object, required): The data object that contains the rubric criteria details.
            category_id (int): The ID of the category the rubric criteria belongs to.
            rubric_id (int, required): The ID of the rubric the criteria is associated with.
            description (str): The description of the rubric criteria.
            report_override_description (str): The report override description of the rubric criteria.
            scale_id (int): The ID of the scale for the rubric criteria.
            type (int): The type of the rubric criteria.
            notes (str): Additional notes for the rubric criteria.
            sort_key (int): The sort key for the rubric criteria.

        Returns:
            pandas.DataFrame: A DataFrame containing the created rubric criteria.
        """

        if 'academics.rubric_criteria:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_criteria:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_criteria"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }
        params = {}

        try:
            response = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame([response])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubric_criteria(self, archived=None, category=None, rubric=None, scale=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        List the rubric criteria for academics.

        Args:
            archived (bool, optional): Filter criteria by archived status.
            category (int, optional): Filter criteria by category ID.
            rubric (int, optional): Filter criteria by rubric ID.
            scale (int, optional): Filter criteria by scale ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of rubric criteria.

        """
        if 'academics.rubric_criteria:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_criteria:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric-criteria"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'archived': archived,
            'category': category,
            'rubric': rubric,
            'scale': scale
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubric_criteria(self, id):
        """
        Get the rubric criteria for a specific ID.

        Args:
            id (int): The ID of the rubric criteria.

        Returns:
            pandas.DataFrame: A DataFrame containing the rubric criteria information.
        """
        if 'Read Academics: Rubric Criteria' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Academics: Rubric Criteria' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_criteria/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_rubric_criteria(self, id, data, x_api_revision, auth_token):
        """
        Update the rubric criteria.

        Args:
            id (int): The ID of the rubric criteria.
            data (dict): The updated data for the rubric criteria. It should contain the following fields:
                - category_id (int): The category ID.
                - rubric_id (int): The rubric ID.
                - description (str): The description.
                - report_override_description (str): The report card description.
                - scale_id (int): The scale ID.
                - type (int): The type.
                - notes (str): The notes.
                - sort_key (int): The sort key.
            x_api_revision (str): The API revision.
            auth_token (str): The authorization token.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated rubric criteria.

        """

        if 'academics.rubric_criteria:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_criteria:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_criteria/{id}"
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'X-API-Revision': x_api_revision,
        }
        params = {}

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                updated_data = response.json().get('data', {})
                df = pd.DataFrame(updated_data)

                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_rubric_scale(self, description, portal_display_format, x_api_revision=None):
        """
        Create a new academic rubric scale.

        Args:
            description (str): Description of the rubric scale.
            portal_display_format (int): Portal assignment criteria grade display field.
            x_api_revision (str, optional): API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the created rubric scale information.
        """
        if 'academics.rubric_scales:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scales:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_scales"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'description': description,
            'portal_display_format': portal_display_format
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubric_scales(self, archived=False, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of rubric scales for academics.

        Args:
            archived (bool, optional): Only return archived rubric scales.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of rubric scales for academics.
        """
        if 'academics.rubric_scales:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scales:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_scales"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {'archived': archived}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubric_scales(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the rubric scales for academics.

        Args:
            id (int, required): The ID of the rubric scale.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response. Allowed value: include.

        Returns:
            pandas.DataFrame: A DataFrame containing the rubric scales for academics.
        """
        if 'academics.rubric_scales:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scales:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_scales/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_rubric_scales(self, id, data):
        """
        Update an academic rubric scale.

        Args:
            id (str): The ID of the rubric scale to update.
            data (dict): The data to update the rubric scale with.
                - description (str): The description of the rubric scale.
                - portal_display_format (int): The display format of the rubric scale in the portal.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated rubric scale.

        """
        if 'academics.rubric_scales:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scales:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_scales/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }
        params = {}

        try:
            response = self.fetch_data_from_api(endpoint, headers, params)
            updated_data = response.json()

            df = pd.DataFrame(updated_data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_rubric_scale_levels(self, description, abbreviation, numeric_value, notes, sort_key, scale_id, scale_description):
        """
        Create new rubric scale levels for academics.

        Args:
            description (str): The description of the rubric scale level.
            abbreviation (str): The abbreviation of the rubric scale level.
            numeric_value (float): The numeric value of the rubric scale level.
            notes (str): Additional notes for the rubric scale level.
            sort_key (int): The sort key of the rubric scale level.
            scale_id (int): The ID of the rubric scale.
            scale_description (str): The description of the rubric scale.

        Returns:
            pandas.DataFrame: A DataFrame containing the created rubric scale level.

        """
        if 'academics.rubric_scale_levels:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scale_levels:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_scale_levels"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'description': description,
            'abbreviation': abbreviation,
            'numeric_value': numeric_value,
            'notes': notes,
            'sort_key': sort_key,
            'scale_id': scale_id,
            'scale_description': scale_description
        }

        try:
            response = self.send_data_to_api(endpoint, headers, data)
            if response.status_code == 201:
                created_data = response.json().get('data', {})
                df = pd.DataFrame([created_data])

                return df
            else:
                print(
                    f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def send_data_to_api(self, endpoint, headers, data):
        """
        Helper function to send data to an API endpoint using the POST method.

        Parameters:
            endpoint (str): The specific API endpoint to send data to.
            headers (dict): Headers required for API authentication and content type.
            data (dict): The data to be sent as the request body.

        Returns:
            requests.Response: The response object of the API request.
        """
        headers['Authorization'] = f"Bearer {self.access_token}"

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)

            return response

        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def get_rubric_scale_levels(self, scale_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of rubric scale levels.

        Args:
            scale_id (int, required): The ID of the scale.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of rubric scale levels.

        """
        if 'academics.rubric_scale_levels:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scale_levels:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubric_scale_levels"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'scale_id': scale_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_rubric_scale_levels(self, id, description, abbreviation, numeric_value, notes, sort_key, scale_id, scale_description, value_lists=None):
        """
        Get the list of rubric scale levels.

        Args:
            id (int): The ID of the rubric scale level.
            description (str): The description of the rubric scale level.
            abbreviation (str): The abbreviation of the rubric scale level.
            numeric_value (float): The numeric value of the rubric scale level.
            notes (str): The notes for the rubric scale level.
            sort_key (int): The sort key of the rubric scale level.
            scale_id (int): The ID of the scale.
            scale_description (str): The description of the scale.
            value_lists (list, optional): Present only with header X-API-Value-Lists = include.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of rubric scale levels.

        """

        if 'Academics: Rubric Scales - Levels' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Academics: Rubric Scales - Levels' to your scopes.")
            return pd.DataFrame()

        endpoint = f"rubric_scale_levels/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': 'include' if value_lists else None
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_rubric_scale_levels(self, id, data):
        """
        Update an academic rubric scale level.

        Args:
            id (str): The ID of the rubric scale level to update.
            data (dict): A dictionary containing the updated data for the rubric scale level. It should have the following keys:
                - description (str): The description of the rubric scale level.
                - abbreviation (str): The abbreviation of the rubric scale level.
                - numeric_value (float): The numeric value of the rubric scale level.
                - notes (str): Any additional notes for the rubric scale level.
                - sort_key (int): The sort key of the rubric scale level.
                - scale_id (int): The ID of the scale associated with the rubric scale level.
                - scale_description (str): The description of the scale associated with the rubric scale level.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated rubric scale level.
        """
        if 'academics.rubric_scale_levels:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubric_scale_levels:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubric_scale_levels/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame([response])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_academics_rubric(self, category_id, description, report_override_description, sort_key, allow_curriculum, x_api_revision=None):
        """
        Create a new academic rubric.

        Args:
            category_id (int): The ID of the rubric category.
            description (str): The description of the rubric.
            report_override_description (str): The override description of the rubric for report cards.
            sort_key (int): The sort key of the rubric.
            allow_curriculum (bool): Flag to allow the rubric to be used in the curriculum.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the created academic rubric.

        """
        if 'academics.rubrics:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubrics:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubrics"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        body_data = {
            'category_id': category_id,
            'description': description,
            'report_override_description': report_override_description,
            'sort_key': sort_key,
            'allow_curriculum': allow_curriculum
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, data=body_data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_rubrics(self, archived=None, category=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic rubrics.

        Args:
            archived (bool, optional): Indicates whether to include archived rubrics.
            category (int, optional): The ID of the rubric category.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic rubrics.
        """
        if 'academics.rubrics:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubrics:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/rubrics"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'archived': archived,
            'category': category
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_rubric(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get a specific rubric by ID.

        Args:
            id (int): The ID of the rubric to retrieve.
            x_api_revision (str, optional): The API revision version.
            x_api_value_lists (str, optional): The value lists for the rubric.

        Returns:
            pandas.DataFrame: A DataFrame containing the requested rubric data.

        """
        if 'academics.rubrics:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.rubrics:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubrics/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_academics_rubrics(self, id, data, x_api_revision):
        """
        Update an academic rubric.

        Args:
            id (int): The ID of the rubric to update.
            data (dict): The data to update the rubric with.
                - category_id (int): The ID of the category.
                - description (str): The description of the rubric.
                - report_override_description (str): The report card description of the rubric.
                - sort_key (int): The sort key of the rubric.
                - allow_curriculum (bool): Whether curriculum is allowed for the rubric.
            x_api_revision (str): API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated academic rubric.

        """
        if 'academics.rubrics:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.rubrics:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/rubrics/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data=data, method='PATCH')
            df = pd.DataFrame([response])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_subjects(self, department_id=None, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, school_level_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic subjects.

        Args:
            department_id (int, optional): The ID of the department.
            last_modified_date (str, optional): Only return subjects that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return subjects that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return subjects that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            school_level_id (int, optional): The ID of the school level.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic subjects.

        """
        if 'academics.subjects:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.subjects:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/subjects"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'department_id': department_id,
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'school_level.id': school_level_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_academics_subjects(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the academic subject with the specified ID.

        Args:
            id (int): The ID of the academic subject.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the academic subject.

        """
        if 'academics.subjects:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'academics.subjects:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"academics/subjects/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_applicant_relationship(self, applicant_id, data):
        """
        Create an admission applicant relationship.

        Args:
            applicant_id (int): The ID of the applicant.
            data (dict): The data for creating the relationship.
                - related_person_id (int, required): The ID of the related person.
                - relationship (int, required): The ID of the relationship.
                - legal_custody (bool): Whether the related person has legal custody.
                - admissions_access (bool): Whether the related person has admissions access.

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission applicant relationship.

        """
        if 'Admission: Applicant Relationships:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Admission: Applicant Relationships:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': data.get('X-API-Revision')
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, json=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_applicant_relationships(self, applicant_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission applicant relationships.

        Args:
            applicant_id (int): The ID of the applicant person.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission applicant relationships.
        """
        if 'admission.applicants.relationships:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.applicants.relationships:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_applicant_relationships(self, applicant_id, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the list of admission applicant relationships.

        Args:
            applicant_id (int): The ID of the applicant.
            id (int): The ID of the relationship.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value list.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission applicant relationships.

        """
        if 'Admission: Applicant Relationships' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Admission: Applicant Relationships' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}/relationships/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_applicant_relationships(self, applicant_id, id, data):
        """
        Update the relationships of an admission applicant.

        Args:
            applicant_id (int): The ID of the admission applicant.
            id (int): The ID of the relationship to be updated.
            data (dict): The data to update the relationship. It should have the following keys:
                - related_person_id (int): The ID of the related person.
                - relationship (int): The ID of the relationship type.
                - legal_custody (bool): Whether the related person has legal custody.
                - admissions_access (bool): Whether the related person has access to admissions data.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated relationship information.

        """
        if 'admission.applicants.relationships:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.applicants.relationships:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}/relationships/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, method='PATCH')
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_applicants(self, household_id, address_1, address_2, address_3, city, state, postal_code, country, name_prefix, first_name, middle_name, last_name, name_suffix, nick_name, gender, pronouns, ethnicity, date_of_birth, email, phone_mobile, current_grade, application_id, year_applying_for, month_applying_for, grade_applying_for, resident_status_applying_for, campus_applying_for, student_group_applying_for, admission_source, candidate_pool, requesting_financial_aid, admission_lead_date, inquiry_date, visit_date, application_date, application_status, application_decision_date, application_decision_response, application_decision_response_date, x_api_revision=None, x_api_value_lists=None):
        """
        Create admission applicants.

        Args:
            household_id (int): The ID of the household.
            address_1 (str): The first line of the address.
            address_2 (str): The second line of the address.
            address_3 (str): The third line of the address.
            city (str): The city of the address.
            state (str): The state of the address.
            postal_code (str): The postal code of the address.
            country (int): The ID of the country.
            name_prefix (int): The ID of the name prefix.
            first_name (str): The first name.
            middle_name (str): The middle name.
            last_name (str): The last name.
            name_suffix (int): The ID of the name suffix.
            nick_name (str): The nick name.
            gender (int): The ID of the gender.
            pronouns (int): The ID of the pronouns.
            ethnicity (int): The ID of the ethnicity.
            date_of_birth (str): The date of birth. Format: "YYYY-MM-DD".
            email (str): The email address.
            phone_mobile (str): The mobile phone number.
            current_grade (int): The ID of the current grade.
            application_id (int): The ID of the application.
            year_applying_for (int): The year applying for.
            month_applying_for (int): The month applying for.
            grade_applying_for (int): The ID of the grade applying for.
            resident_status_applying_for (int): The ID of the resident status applying for.
            campus_applying_for (int): The ID of the campus applying for.
            student_group_applying_for (int): The ID of the student group applying for.
            admission_source (int): The ID of the admission source.
            candidate_pool (int): The ID of the candidate pool.
            requesting_financial_aid (bool): Whether financial aid is requested.
            admission_lead_date (str): The admission lead date. Format: "YYYY-MM-DD".
            inquiry_date (str): The inquiry date. Format: "YYYY-MM-DD".
            visit_date (str): The visit date. Format: "YYYY-MM-DD".
            application_date (str): The application date. Format: "YYYY-MM-DD".
            application_status (int): The ID of the application status.
            application_decision_date (str): The application decision date. Format: "YYYY-MM-DD".
            application_decision_response (int): The ID of the application decision response.
            application_decision_response_date (str): The application decision response date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission applicants.

        """
        if 'create_admission_applicants' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'create_admission_applicants' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/applicants"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'household_id': household_id,
            'address_1': address_1,
            'address_2': address_2,
            'address_3': address_3,
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'country': country,
            'name_prefix': name_prefix,
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'name_suffix': name_suffix,
            'nick_name': nick_name,
            'gender': gender,
            'pronouns': pronouns,
            'ethnicity': ethnicity,
            'date_of_birth': date_of_birth,
            'email': email,
            'phone_mobile': phone_mobile,
            'current_grade': current_grade,
            'application_id': application_id,
            'year_applying_for': year_applying_for,
            'month_applying_for': month_applying_for,
            'grade_applying_for': grade_applying_for,
            'resident_status_applying_for': resident_status_applying_for,
            'campus_applying_for': campus_applying_for,
            'student_group_applying_for': student_group_applying_for,
            'admission_source': admission_source,
            'candidate_pool': candidate_pool,
            'requesting_financial_aid': requesting_financial_aid,
            'admission_lead_date': admission_lead_date,
            'inquiry_date': inquiry_date,
            'visit_date': visit_date,
            'application_date': application_date,
            'application_status': application_status,
            'application_decision_date': application_decision_date,
            'application_decision_response': application_decision_response,
            'application_decision_response_date': application_decision_response_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_applicants(self, date_of_birth=None, email=None, first_name=None, last_name=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission applicants.

        Args:
            date_of_birth (str, required): Birthday of the applicant. Format: "YYYY-MM-DD".
            email (str, required): Email address of the applicant.
            first_name (str, required): First name of the applicant.
            last_name (str, required): Last name of the applicant.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission applicants.

        """
        if 'admission.applicants:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.applicants:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/applicants"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'date_of_birth': date_of_birth,
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_applicant(self, applicant_id, data=None, household_id=None, name_prefix=None, first_name=None, middle_name=None, last_name=None, name_suffix=None, nick_name=None, gender=None, pronouns=None, ethnicity=None, date_of_birth=None, email=None, mobile_phone=None, current_grade=None, x_api_revision=None, x_page_number=1, x_page_size=1000):
        """
        Update an admission applicant.

        Args:
            applicant_id (int): The ID of the applicant to update.
            data (object, optional): The data object to update the applicant.
            household_id (int, optional): The ID of the household associated with the applicant.
            name_prefix (int, optional): The ID of the name prefix.
            first_name (str, optional): The first name of the applicant.
            middle_name (str, optional): The middle name of the applicant.
            last_name (str, optional): The last name of the applicant.
            name_suffix (int, optional): The ID of the name suffix.
            nick_name (str, optional): The nick name of the applicant.
            gender (int, optional): The ID of the gender.
            pronouns (int, optional): The ID of the pronouns.
            ethnicity (int, optional): The ID of the ethnicity.
            date_of_birth (str, optional): The date of birth of the applicant. Format: "YYYY-MM-DD".
            email (str, optional): The email of the applicant.
            mobile_phone (str, optional): The mobile phone number of the applicant.
            current_grade (int, optional): The ID of the current grade.
            x_api_revision (str, optional): The API revision.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission applicant.

        """
        if 'admission.applicants:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.applicants:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'data': data,
            'household_id': household_id,
            'name_prefix': name_prefix,
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'name_suffix': name_suffix,
            'nick_name': nick_name,
            'gender': gender,
            'pronouns': pronouns,
            'ethnicity': ethnicity,
            'date_of_birth': date_of_birth,
            'email': email,
            'mobile_phone': mobile_phone,
            'current_grade': current_grade
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_application_checklists(self, application_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of application checklists.

        Args:
            application_id (int, required): The ID of the application.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of application checklists.

        """
        if 'application_checklists:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'application_checklists:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"application_checklists/{application_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def admission_application_checklists_read(self, application_id, id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the checklist items for a specific admission application.

        Args:
            application_id (int): The ID of the admission application.
            id (int): The ID of the checklist item.

        Returns:
            pandas.DataFrame: A DataFrame containing the checklist items.

        """
        if 'admission.applications.checklists:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.applications.checklists:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applications/{application_id}/checklists"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'id': id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_application_checklists(self, application_id, id, data):
        """
        Update the admission application checklists.

        Args:
            application_id (int): The ID of the application.
            id (int): The ID of the checklist item.
            data (dict): A dictionary containing the updated checklist item data.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission application checklists.

        """
        if 'admission.application_checklists:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.application_checklists:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applications/{application_id}/checklists/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': data['X-API-Revision'],
            'Auth Token': data['Auth Token']
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_applications(self, data):
        """
        Create admission applications.

        Args:
            data (dict): The data for creating admission applications. The required keys and types are:
                - applicant_id (int): Applicant ID.
                - year_applying_for (int): Year Applying For.
                - month_applying_for (int): Month Applying For.
                - grade_applying_for (int): Grade Applying For.
                - resident_status_applying_for (int): Resident Status Applying For.
                - campus_applying_for (int): Campus Applying For.
                - student_group_applying_for (int): Student Group Applying For.
                - admission_source (int): Admission Source.
                - candidate_pool (int): Candidate Pool.
                - admission_lead_date (str): Admission Lead Date.
                - inquiry_date (str): Inquiry Date.
                - visit_date (str): Visit Date.
                - application_date (str): Application Date.
                - requesting_financial_aid (bool): Requesting Financial Aid.
                - application_status (int): Application Status.
                - application_decision_date (str): Application Decision Date.
                - application_decision_response (int): Application Decision Response.
                - application_decision_response_date (str): Application Decision Response Date.

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission applications.

        """
        if 'admission.applications:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.applications:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/applications"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'API Revision'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_applications(self, applicant_id=None, application_status=None, first_name=None, last_name=None, year_applying_for=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of admission applications.

        Args:
            applicant_id (str, optional): The ID of the applicant.
            application_status (str, optional): The status of the application.
            first_name (str, optional): The first name of the applicant.
            last_name (str, optional): The last name of the applicant.
            year_applying_for (int, optional): The year the applicant is applying for.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission applications.

        """
        if 'Admission: Applications' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Admission: Applications' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/applications"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'applicant_id': applicant_id,
            'application_status': application_status,
            'first_name': first_name,
            'last_name': last_name,
            'year_applying_for': year_applying_for
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    class MyClass:
        def get_admission_application(self, application_id=None, x_api_revision=None, x_api_value_lists=None):
            """
            Get the admission application.

            Args:
                application_id (int): The ID of the application.
                x_api_revision (str, optional): The API revision.
                x_api_value_lists (str, optional): Include value lists in the response.

            Returns:
                pandas.DataFrame: A DataFrame containing the admission application.

            """
            if 'admission.applications:read' not in self.scopes:
                print(
                    "Error: You don't have the required scope for this endpoint. Please add 'admission.applications:read' to your scopes.")
                return pd.DataFrame()

            endpoint = f"admission/applications/{application_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-API-Revision': x_api_revision,
                'X-API-Value-Lists': x_api_value_lists
            }
            params = {}

            try:
                data = self.fetch_data_from_api(endpoint, headers, params)
                df = pd.DataFrame(data)

                return df

            except Exception as e:
                print(f"Error: {str(e)}")
                return pd.DataFrame()

    def update_admission_applications(self, application_id, data):
        """
        Update an admission application.

        Args:
            application_id (int): The ID of the application to update.
            data (dict): The data to update the application with. Required fields:
                - applicant_id (int): Applicant ID
                - year_applying_for (int): Year Applying For
                - month_applying_for (int): Month Applying For
                - grade_applying_for (int): Grade Applying For
                - resident_status_applying_for (int): Resident Status Applying For
                - campus_applying_for (int): Campus Applying For
                - student_group_applying_for (int): Student Group Applying For
                - admission_source (int): Admission Source
                - candidate_pool (int): Candidate Pool
                - admission_lead_date (str): Admission Lead Date
                - inquiry_date (str): Inquiry Date
                - visit_date (str): Visit Date
                - application_date (str): Application Date
                - requesting_financial_aid (bool): Requesting Financial Aid
                - application_status (int): Application Status
                - application_decision_date (str): Application Decision Date
                - application_decision_response (int): Application Decision Response
                - application_decision_response_date (str): Application Decision Response Date

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission application.
        """
        if 'update:admission_applications' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'update:admission_applications' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission_applications/{application_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'API Revision'
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                updated_data = response.json()
                df = pd.DataFrame(updated_data)

                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_citizenship(self, person_id, country, is_primary, passport_number, passport_issue_date, passport_issuing_authority, passport_expiration_date):
        """
        Create a new admission citizenship.

        Args:
            person_id (int): Person ID. Required.
            country (int): Country of Citizenship. Required.
            is_primary (bool): Primary Citizenship. Required.
            passport_number (str): Passport Number. Required.
            passport_issue_date (str): Passport Issue Date. Required.
            passport_issuing_authority (str): Passport Issuing Authority. Required.
            passport_expiration_date (str): Passport Expiration Date. Required.

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission citizenship.

        """
        if 'admission.citizenships:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.citizenships:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/citizenships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-API-Revision': 'string'
        }
        data = {
            'person_id': person_id,
            'country': country,
            'is_primary': is_primary,
            'passport_number': passport_number,
            'passport_issue_date': passport_issue_date,
            'passport_issuing_authority': passport_issuing_authority,
            'passport_expiration_date': passport_expiration_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, json=data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_citizenships(self, person_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission citizenships for a specific person.

        Args:
            person_id (int): Person ID.

        Optional Args:
            x_api_revision (str): API Revision.
            x_api_value_lists (str): Include Value Lists in response. Allowed value: include.
            x_page_number (int): Page number. Default: 1.
            x_page_size (int): Number of records per page (for collection endpoints). Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission citizenships for the person.
        """
        if 'admission.citizenships:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.citizenships:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/citizenships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_citizenships(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a specific admission citizenship or a list of admission citizenships.

        Args:
            id (int, optional): The ID of the admission citizenship.
            x_api_revision (str, optional): The API revision for the request.
            x_api_value_lists (str, optional): Include value lists in the response. Allowed value: "include".

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the admission citizenship(s).

        """
        if 'admission.citizenships:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.citizenships:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/citizenships/{id}" if id else "admission/citizenships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            if id:
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_citizenships(self, id, data):
        """
        Update the citizenships for an admission.

        Args:
            id (int): The ID of the admission.
            data (dict): The data for updating citizenships. It should have the following keys:
                - person_id (int): The ID of the person.
                - country (int): The ID of the country.
                - is_primary (bool): Indicates if it is the primary citizenship.
                - passport_number (str): The passport number.
                - passport_issue_date (str): The passport issue date in the format "YYYY-MM-DD".
                - passport_issuing_authority (str): The authority issuing the passport.
                - passport_expiration_date (str): The passport expiration date in the format "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the updated citizenships for the admission.
        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admissions/{id}/citizenships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, params={}, method='PATCH', json=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_configuration_checklists(self, school_year=None, category_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of admission configuration checklists.

        Args:
            school_year (int, optional): The school year for which to retrieve the checklists.
            category_id (int, optional): The category ID of the checklists.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response. Allowed value: 'include'.
            x_page_number (int, optional): The page number to fetch. Default is 1.
            x_page_size (int, optional): The number of records per page. Minimum is 1, maximum is 1000. Default is 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission configuration checklists.

        """
        if 'admission.config.years.checklists:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.config.years.checklists:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/configuration/checklists"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'school_year': school_year,
            'category_id': category_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_configuration_checklists(self, id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of admission configuration checklists.

        Args:
            id (int, optional): The Registration Season Checklist Item ID.
            school_year (int, optional): The School Year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission configuration checklists.

        """
        if 'Read Admission: Configuration - Checklists' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Read Admission: Configuration - Checklists' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/configuration/checklists"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'id': id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_configuration_years(self, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission configuration years.

        Args:
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.
            x_page_number (int, optional): Page number. Default: 1.
            x_page_size (int, optional): Number of records per page. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission configuration years.

        """
        if 'admission.config.years:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.config.years:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_admission_configuration_years"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_config_years(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the admission configuration years.

        Args:
            id (int, optional): The ID of the admission configuration year.

        Returns:
            pandas.DataFrame: A DataFrame containing the admission configuration years.

        """
        if 'Admission: Configuration - Years' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Admission: Configuration - Years' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/config_years/{id}" if id else "admission/config_years"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_household_members(self, household_id, first_name=None, last_name=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of household members for a specific admission household.

        Args:
            household_id (int): The ID of the admission household.
            first_name (str, optional): Only return household members with the specified first name.
            last_name (str, optional): Only return household members with the specified last name.
            x_api_revision (str, optional): The API revision value.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of household members.

        """
        if 'admission.households.members:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.households.members:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/households/{household_id}/members"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'first_name': first_name,
            'last_name': last_name
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_households(self, address_1=None, address_2=None, address_3=None, city=None, country=None, name=None, postal_code=None, state=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission households.

        Args:
            address_1 (str, optional): Address 1.
            address_2 (str, optional): Address 2.
            address_3 (str, optional): Address 3.
            city (str, optional): City.
            country (int, optional): Country.
            name (str, optional): Name.
            postal_code (str, optional): Postal Code.
            state (str, optional): State.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission households.

        """
        if 'admission.households:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.households:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/households"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'address_1': address_1,
            'address_2': address_2,
            'address_3': address_3,
            'city': city,
            'country': country,
            'name': name,
            'postal_code': postal_code,
            'state': state
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def admission_households_read(self, id):
        """
        Get information about a specific household.

        Args:
            id (int): The ID of the household. (required)

        Returns:
            pandas.DataFrame: A DataFrame with information about the household.
        """
        if 'admission.households:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.households:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/households/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': "string",
            'X-API-Value-Lists': "string"
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_households(self, id, data, x_api_revision=None):
        """
        Update an admission household.

        Args:
            id (str): The ID of the admission household to update.
            data (dict): The updated data for the admission household.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission household.

        """
        if 'Admission: Households' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Admission: Households' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/households/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, method='PATCH', data=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_languages(self, person_id, language, is_primary, reading_proficiency, writing_proficiency, speaking_proficiency, listening_proficiency, years_studying, spoken_at_home, notes):
        """
        Create admission languages for a person.

        Args:
            person_id (int): The ID of the person.
            language (int): The ID of the language.
            is_primary (bool): The primary code.
            reading_proficiency (int): The reading proficiency.
            writing_proficiency (int): The writing proficiency.
            speaking_proficiency (int): The speaking proficiency.
            listening_proficiency (int): The listening proficiency.
            years_studying (int): The years studying.
            spoken_at_home (bool): Spoken at home.
            notes (str): Additional notes.

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission languages.
        """
        if 'admission.languages:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.languages:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/languages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'API Revision'
        }
        data = {
            "person_id": person_id,
            "language": language,
            "is_primary": is_primary,
            "reading_proficiency": reading_proficiency,
            "writing_proficiency": writing_proficiency,
            "speaking_proficiency": speaking_proficiency,
            "listening_proficiency": listening_proficiency,
            "years_studying": years_studying,
            "spoken_at_home": spoken_at_home,
            "notes": notes
        }

        try:
            data = self.fetch_data_from_api(
                endpoint, headers, json.dumps(data))
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_languages(self, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of admission languages.

        Args:
            person_id (int, optional): The ID of the person.
            x_api_revision (str, optional): The version of the API.
            x_api_value_lists (str, optional): The value lists for the API.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission languages.

        """
        if 'Admission: Languages' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Admission: Languages' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/languages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def admission_languages_read(self, id=None):
        """
        Get the information about an admission language.

        Args:
            id (int): The ID of the admission language.

        Returns:
            pandas.DataFrame: A DataFrame containing the information about the admission language.

        """
        if 'admission.languages:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.languages:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/languages/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string',
            'X-API-Value-Lists': 'string',
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_languages(self, id, person_id, language, is_primary, reading_proficiency, writing_proficiency, speaking_proficiency, listening_proficiency, years_studying, spoken_at_home, notes, x_api_revision):
        """
        Update the admission languages for a specific ID.

        Args:
            id (str): The ID of the admission.
            person_id (int): Person ID.
            language (int): Language.
            is_primary (bool): Primary Code.
            reading_proficiency (int): Reading Proficiency.
            writing_proficiency (int): Writing Proficiency.
            speaking_proficiency (int): Speaking Proficiency.
            listening_proficiency (int): Listening Proficiency.
            years_studying (int): Years Studying.
            spoken_at_home (bool): Spoken At Home.
            notes (str): Notes.
            x_api_revision (str): X-API-Revision value.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission languages.

        """

        endpoint = f"admissions/{id}/languages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'person_id': person_id,
            'language': language,
            'is_primary': is_primary,
            'reading_proficiency': reading_proficiency,
            'writing_proficiency': writing_proficiency,
            'speaking_proficiency': speaking_proficiency,
            'listening_proficiency': listening_proficiency,
            'years_studying': years_studying,
            'spoken_at_home': spoken_at_home,
            'notes': notes
        }

        try:
            self.fetch_data_from_api(endpoint, headers, data)
            return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_relative_relationships(self, relative_id, data, x_api_revision=None):
        """
        Create admission relative relationships.

        Args:
            relative_id (int): The ID of the relative.
            data (dict): The data for creating the admission relative relationships.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the created admission relative relationships.
        """
        if 'admission.relatives.relationships:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.relatives.relationships:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/relatives/{relative_id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_relative_relationships(self, relative_id, x_api_revision, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of admission relative relationships.

        Args:
            relative_id (int): The ID of the relative.
            x_api_revision (str): API revision.
            x_api_value_lists (str, optional): Include value lists in the response. Allowed values: include.
            x_page_number (int, optional): Page number. Must be greater than or equal to 1. Default is 1.
            x_page_size (int, optional): Number of records per page. Must be greater than or equal to 1 and less than or equal to 1000. Default is 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission relative relationships.
        """

        endpoint = f"admission/relatives/{relative_id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_relative_relationships(self, relative_id, id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of relative relationships for an admission.

        Args:
            relative_id (int): The ID of the relative.
            id (int): The ID of the admission.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of relative relationships for an admission.

        """
        if 'admission.relatives.relationships:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'admission.relatives.relationships:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/{id}/relative/{relative_id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_relative_relationships(self, relative_id, id, data, x_api_revision=None):
        """
        Update the admission relative relationships.

        Args:
            relative_id (int): The ID of the relative.
            id (int): The ID of the relationship.
            data (dict): The data to update the relationship. It should contain the 'related_person_id' and 'relationship' as integers.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission relative relationships.

        """
        if 'admission.relative_relationships:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.relative_relationships:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/relative_relationships/{relative_id}/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_admission_relative(self, data, x_api_revision):
        """
        Create an admission relative.

        Args:
            data (dict): The data for creating the admission relative. The keys are as follows:
                - household_id (int): Required. The household ID.
                - address_1 (str): Optional. Address Line 1.
                - address_2 (str): Optional. Address Line 2.
                - address_3 (str): Optional. Address Line 3.
                - city (str): Optional. The city.
                - state (str): Optional. The state.
                - postal_code (str): Optional. The postal code.
                - country (int): Required. The country.
                - name_prefix (int): Required. The name prefix.
                - first_name (str): Optional. The first name.
                - middle_name (str): Optional. The middle name.
                - last_name (str): Required. The last name.
                - name_suffix (str): Required. The name suffix.
                - nick_name (str): Optional. The nick name.
                - maiden_name (str): Optional. The maiden name.
                - marital_status (int): Required. The marital status.
                - pronouns (int): Required. The pronouns.
                - gender (int): Required. The gender.
                - ethnicity (int): Required. The ethnicity.
                - date_of_birth (str): Optional. The date of birth. Format: "YYYY-MM-DD".
                - place_of_birth (str): Optional. The place of birth.
                - date_of_death (str): Optional. The date of death. Format: "YYYY-MM-DD".
                - graduation_year (int): Required. The graduation year.
                - email (str): Optional. The email address.
                - mobile_phone (str): Optional. The mobile phone number.
                - work_phone (str): Optional. The work phone number.
                - applicant_id (int): Required. The applicant ID.
                - relationship (int): Required. The relationship.
                - legal_custody (bool): Required. Legal custody.
                - admissions_access (bool): Required. Admissions access.

            x_api_revision (str): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the created admission relative.

        """
        if 'Admission: Relatives:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Admission: Relatives:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "admission/relatives"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data=data, method='POST')
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_relatives(self, id):
        """
        Get the admission relative with the specified ID.

        Args:
            id (int): The ID of the admission relative.

        Returns:
            pandas.DataFrame: A DataFrame containing the admission relative information.
        """
        if 'admission.relatives:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.relatives:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/relatives/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_athletics_rosters(self, internal_class_id, person_id, first_name, last_name, grade_level_id, currently_enrolled, data=None):
        """
        Create athletics rosters.

        Args:
            internal_class_id (int): The internal class ID.
            person_id (int): The person ID.
            first_name (str): The first name.
            last_name (str): The last name.
            grade_level_id (int): The grade level ID.
            currently_enrolled (bool): Whether the person is currently enrolled.
            data (dict, optional): Additional data for creating the athletics rosters. Default is None.

        Returns:
            pandas.DataFrame: A DataFrame containing the created athletics rosters.

        """
        if 'athletics.rosters:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.rosters:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/rosters"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': "string"
        }

        body_data = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'first_name': first_name,
            'last_name': last_name,
            'grade_level_id': grade_level_id,
            'currently_enrolled': currently_enrolled,
        }

        if data is not None:
            body_data.update(data)

        try:
            self.post_data_to_api(endpoint, headers, body_data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_rosters(self, id):
        """
        Get the roster for a specific athletics enrollment.

        Args:
            id (int): The ID of the athletics enrollment.

        Returns:
            pandas.DataFrame: A DataFrame containing the roster information.

        """
        if 'athletics.rosters:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.rosters:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/rosters/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params=None)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_athletics_rosters(self, id, data, x_api_revision=None):
        """
        Update the athletics rosters for a specific enrollment.

        Args:
            id (int): The ID of the enrollment.
            data (dict): The data to update for the enrollment.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated athletics rosters.

        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/rosters/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            if isinstance(response, dict):
                return pd.DataFrame([response])
            else:
                return pd.DataFrame(response)

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_sports(self, gender=None, school_level=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        List athletics sports.

        Args:
            gender (int, optional): The gender of the sports.
            school_level (string, optional): The school level of the sports.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of athletics sports.

        """
        if 'athletics.sports:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.sports:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/sports"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'gender': gender,
            'school_level': school_level
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_sports(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a specific athletics sport.

        Args:
            id (int): The internal course ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the athletics sport.
        """
        if 'Athletics: Sports' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Athletics: Sports' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/sports/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_athletics_sports(self, id, data):
        """
        Update the details of an athletics sport.

        Args:
            id (int): The ID of the athletics sport to be updated.
            data (dict): The data to be updated. It should include the following fields:
                - description (str): The description of the athletics sport.
                - abbreviation (str): The abbreviation of the athletics sport.
                - school_level (str): The school level of the athletics sport.
                - gender (int): The gender of the athletics sport.
                - subject_id (int): The ID of the subject related to the athletics sport.
                - subject_description (str): The description of the subject related to the athletics sport.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated details of the athletics sport.

        """
        if 'athletics.sports:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.sports:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/sports/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame([response])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_athletics_sports(self, data):
        """
        Create a new athletics sport.

        Args:
            data (dict): A dictionary containing the details of the athletics sport.
                - description (str): The description of the sport.
                - abbreviation (str): The abbreviation of the sport.
                - gender (int): The gender of the sport.
                - subject_id (int): The ID of the subject associated with the sport.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the created athletics sport.

        """
        if 'athletics.sports:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'athletics.sports:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/sports/"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string',
        }

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=data
            )

            if response.status_code == 201:
                sport_data = response.json()
                df = pd.DataFrame([sport_data])
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_athletics_teams(self, school_level, internal_sport_id, team_id, description, sport_id, head_coach_id, assistant_coach_id, begin_date, end_date, x_api_revision=None, x_api_value_lists=None):
        """
        Create athletics teams.

        Args:
            school_level (int): The school level.
            internal_sport_id (int): The internal sport ID.
            team_id (str): The team ID.
            description (str): The team description.
            sport_id (int): The sport.
            head_coach_id (int): The coach ID.
            assistant_coach_id (int): The assistant coach ID.
            begin_date (str): The begin date. Format: "YYYY-MM-DD".
            end_date (str): The end date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the created athletics teams.
        """
        if 'athletics.teams:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.teams:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/teams"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
        }
        data = {
            'school_level': school_level,
            'internal_sport_id': internal_sport_id,
            'team_id': team_id,
            'description': description,
            'sport_id': sport_id,
            'head_coach_id': head_coach_id,
            'assistant_coach_id': assistant_coach_id,
            'begin_date': begin_date,
            'end_date': end_date
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_teams(self, head_coach_id=None, internal_sport_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of athletics teams.

        Args:
            head_coach_id (int, optional): The coach ID of the head coach.
            internal_sport_id (int, optional): The sport ID.
            school_year (int, optional): The school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of athletics teams.

        """
        if 'athletics.teams:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.teams:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/teams"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'head_coach_id': head_coach_id,
            'internal_sport_id': internal_sport_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_teams(self, id):
        """
        Get the details of an athletics team.

        Args:
            id (string): The ID of the team.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the athletics team.
        """
        if 'athletics.teams:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'athletics.teams:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/teams/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_athletics_teams(self, id, x_api_revision=None, data=None):
        """
        Update an athletics team.

        Args:
            id (int): The internal Class ID of the team to update.
            x_api_revision (str, optional): The API Revision.
            data (dict, optional): The data to update the athletics team.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated athletics team details.
        """

        if 'athletics.teams:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'athletics.teams:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"athletics/teams/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
        }
        params = {}

        try:
            response = self.fetch_data_from_api(endpoint, headers, params)

            if response:
                headers['Content-Type'] = 'application/json'

                response = requests.patch(
                    f"{self.base_url}/{endpoint}", headers=headers, json=data)

                if response.status_code == 200:
                    df = pd.DataFrame(response.json().get('data', []))

                    return df
                else:
                    print(f"Error: {response.status_code} - {response.text}")
            else:
                print("Error: Athletics team not found.")
        except Exception as e:
            print(f"Error: {str(e)}")

        return pd.DataFrame()

    def create_behavior(self, data):
        """
        Create a behavior record.

        Args:
            data (dict): A dictionary containing the data for the behavior record.
                - incident_date (str): The date of the incident. Format: "YYYY-MM-DD".
                - incident_type (int): The type of the incident.
                - student_id (int): The ID of the student involved in the incident.
                - reporting_person_id (int): The ID of the person reporting the incident.
                - assigned_to_person_id (int): The ID of the person assigned to handle the incident.
                - internal_class_id (int): The ID of the internal class associated with the incident.
                - class_name (str): The name of the class associated with the incident.
                - incident_notes (str): Additional notes about the incident.
                - status (int): The status of the incident.
                - status_date (str): The date of the incident status. Format: "YYYY-MM-DD".
                - outcome_type (int): The type of outcome for the incident.
                - outcome_date (str): The date of the incident outcome. Format: "YYYY-MM-DD".
                - outcome_notes (str): Additional notes about the incident outcome.
                - follow_up_status (int): The status of the incident follow-up.
                - follow_up_status_date (str): The date of the incident follow-up status. Format: "YYYY-MM-DD".
                - last_modified_date (str): The date of the last modification. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the created behavior record.

        """
        if 'behavior:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'behavior:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "behaviors/create_behavior"
        headers = {
            'X-API-Revision': 'string',
            'Token': 'string',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)

            if response.status_code == 200:
                return pd.DataFrame(response.json())

            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_behavior(self, grading_period=None, incident_type=None, internal_class_id=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, outcome_type=None, school_year=None, status=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of behaviors.

        Args:
            grading_period (int, optional): The grading period of the behavior.
            incident_type (int, optional): The type of the incident.
            internal_class_id (int, optional): The ID of the internal class.
            on_or_after_last_modified_date (str, optional): Only return behaviors that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return behaviors that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            outcome_type (int, optional): The type of the outcome.
            school_year (int, optional): The school year of the behavior.
            status (int, optional): The status of the behavior.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of behaviors.

        """
        if 'behavior:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'behavior:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "behavior/list"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'grading_period': grading_period,
            'incident_type': incident_type,
            'internal_class_id': internal_class_id,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'outcome_type': outcome_type,
            'school_year': school_year,
            'status': status
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_behavior(self, id=None,
                     incident_date=None,
                     incident_type=None,
                     student_id=None,
                     reporting_person_id=None,
                     assigned_to_person_id=None,
                     internal_class_id=None,
                     class_name=None,
                     incident_notes=None,
                     behavior_points=None,
                     status=None,
                     status_date=None,
                     outcome_type=None,
                     outcome_date=None,
                     outcome_notes=None,
                     follow_up_status=None,
                     follow_up_status_date=None,
                     last_modified_date=None,
                     value_lists=None,
                     x_api_revision=None,
                     x_api_value_lists=None,
                     x_page_number=1,
                     x_page_size=1000):
        """
        Get behavior data.

        Args:
            id (int, optional): Behavior ID.
            incident_date (str, optional): Incident Date (Format: "YYYY-MM-DD").
            incident_type (int, optional): Incident Type.
            student_id (int, optional): Student ID.
            reporting_person_id (int, optional): Reporting Person ID.
            assigned_to_person_id (int, optional): Assigned To Person ID.
            internal_class_id (int, optional): Class ID.
            class_name (str, optional): Description.
            incident_notes (str, optional): Incident Notes.
            behavior_points (int, optional): Behavior Points.
            status (int, optional): Status.
            status_date (str, optional): Status Date (Format: "YYYY-MM-DD").
            outcome_type (int, optional): Outcome Type.
            outcome_date (str, optional): Outcome Date (Format: "YYYY-MM-DD").
            outcome_notes (str, optional): Outcome Notes
            follow_up_status (int, optional): Follow Up Status.
            follow_up_status_date (str, optional): Follow Up Status Date (Format: "YYYY-MM-DD").
            last_modified_date (str, optional): Update Date (Format: "YYYY-MM-DD").
            value_lists (List[Dict[str, Any]], optional): Value lists.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response (Allowed value: "include").
            x_page_number (int, optional): Page number for pagination. Defaults to 1.
            x_page_size (int, optional): Page size for pagination. Defaults to 1000.

        Returns:
            pandas.DataFrame: A DataFrame containing the behavior data.
        """

        if 'behavior:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'behavior:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"behavior/{id}" if id else "behavior"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'incident_date': incident_date,
            'incident_type': incident_type,
            'student_id': student_id,
            'reporting_person_id': reporting_person_id,
            'assigned_to_person_id': assigned_to_person_id,
            'internal_class_id': internal_class_id,
            'class_name': class_name,
            'incident_notes': incident_notes,
            'behavior_points': behavior_points,
            'status': status,
            'status_date': status_date,
            'outcome_type': outcome_type,
            'outcome_date': outcome_date,
            'outcome_notes': outcome_notes,
            'follow_up_status': follow_up_status,
            'follow_up_status_date': follow_up_status_date,
            'last_modified_date': last_modified_date,
            'value_lists': value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_behavior(self, school_route, id, data):
        """
        Update a behavior record.

        Args:
            school_route (str): The route for the specific school.
            id (int): The ID of the behavior record to update.
            data (dict): The data for updating the behavior record. It should include the following keys:
                - incident_date (str): The date of the incident. Format: "YYYY-MM-DD".
                - incident_type (int): The type of the incident.
                - student_id (int): The ID of the student involved in the incident.
                - reporting_person_id (int): The ID of the person who reported the incident.
                - assigned_to_person_id (int): The ID of the person assigned to handle the incident.
                - internal_class_id (int): The ID of the internal class.
                - class_name (str): The name of the class associated with the incident.
                - incident_notes (str): Any notes related to the incident.
                - status (int): The status of the incident.
                - status_date (str): The date when the status was updated. Format: "YYYY-MM-DD".
                - outcome_type (int): The type of the outcome of the incident.
                - outcome_date (str): The date when the outcome was updated. Format: "YYYY-MM-DD".
                - outcome_notes (str): Any notes related to the outcome of the incident.
                - follow_up_status (int): The status of the follow-up for the incident.
                - follow_up_status_date (str): The date when the follow-up status was updated. Format: "YYYY-MM-DD".
                - last_modified_date (str): The date when the record was last modified. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the updated behavior record.
        """

        endpoint = f"{school_route}/behavior/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-API-Revision': 'x_api_revision'
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                behavior_data = response.json().get('data')
                df = pd.DataFrame([behavior_data])

                return df
            else:
                print(
                    f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_dorm_attendance(self, internal_dorm_id, on_or_after_attendance_date=None,
                            on_or_after_last_modified_date=None, on_or_before_attendance_date=None,
                            on_or_before_last_modified_date=None, school_year=None,
                            X_API_Revision=None, X_API_Value_Lists=None, X_Page_Number=1, X_Page_Size=1000):
        """
        Retrieve the list of dorm attendance records.

        Args:
            internal_dorm_id (int): The internal ID of the dorm.
            on_or_after_attendance_date (str, optional): Only return attendance records on or after this date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return attendance records that were last modified on or after this date. Format: "YYYY-MM-DD".
            on_or_before_attendance_date (str, optional): Only return attendance records on or before this date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return attendance records that were last modified on or before this date. Format: "YYYY-MM-DD".
            school_year (int, optional): Only return attendance records from the specified school year.
            X_API_Revision (str, optional): The API revision version.
            X_API_Value_Lists (str, optional): The value lists to include in the response.
            X_Page_Number (int, optional): The page number of the results.
            X_Page_Size (int, optional): The number of records per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of dorm attendance records.
        """
        if 'boarding.dorms.attendance:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'boarding.dorms.attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding/dorms/{internal_dorm_id}/attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': X_API_Revision,
            'X-API-Value-Lists': X_API_Value_Lists,
            'X-Page-Number': str(X_Page_Number),
            'X-Page-Size': str(X_Page_Size)
        }
        params = {
            'on_or_after_attendance_date': on_or_after_attendance_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_attendance_date': on_or_before_attendance_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    # def boarding_dorm_attendance(self, id, internal_dorm_id, dorm_id, student_id, attendance_date, block, start_time, end_time, status, notes, last_modified_date, value_lists=None, x_api_revision=None):
    #     """
    #     Get attendance data for a specific boarding dorm.

    #     Args:
    #         id (int): Class Attendance ID.
    #         internal_dorm_id (int): Internal Class ID.
    #         dorm_id (int): Dorm ID.
    #         student_id (int): Person ID.
    #         attendance_date (str): Attendance Date in the format "YYYY-MM-DD".
    #         block (int): Block.
    #         start_time (str): Class Begin Time in the format "HH:MM".
    #         end_time (str): Class End Time in the format "HH:MM".
    #         status (int): Status.
    #         notes (str): Notes.
    #         last_modified_date (str): Last Modified Date in the format "YYYY-MM-DD".
    #         value_lists (list of objects, optional): Value Lists to include in the response.
    #         x_api_revision (str, optional): API Revision.

    #     Returns:
    #         pandas.DataFrame: A DataFrame containing the attendance data for the boarding dorm.
    #     """

    #     if 'boarding_dorm_attendance:get' not in self.scopes:
    #         print("Error: You don't have the required scope for this endpoint. Please add 'boarding_dorm_attendance:get' to your scopes.")
    #         return pd.DataFrame()

    #     endpoint = f"boarding_dorm_attendance/{id}

    def update_boarding_dorm_attendance(self, internal_dorm_id, id, attendance_date, block, status, notes, x_api_revision):
        """
        Update the attendance record for a specific boarding dorm.

        Args:
            internal_dorm_id (str): The internal ID of the boarding dorm.
            id (str): The ID of the attendance record to be updated.
            attendance_date (str): The date of the attendance record. Format: "YYYY-MM-DD".
            block (int): The block number for the attendance record.
            status (int): The status of the attendance record.
            notes (str): Additional notes for the attendance record.
            x_api_revision (str): The API revision number.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated attendance record.

        """
        if 'boarding.dorms.attendance:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'boarding.dorms.attendance:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding/dorms/{internal_dorm_id}/attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        params = {}

        body = {
            'data': {
                'attendance_date': attendance_date,
                'block': block,
                'status': status,
                'notes': notes
            }
        }

        try:
            data = self.fetch_data_from_api(
                endpoint, headers, params, method='PATCH', json_body=body)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_boarding_dorm_students(self, internal_dorm_id, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of students in a boarding dorm.

        Args:
            internal_dorm_id (int): The internal ID of the dorm.
            school_year (str, optional): Only return students enrolled in the specified school year.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response. Allowed value: "include".
            x_page_number (int, optional): The page number to retrieve. Must be greater than or equal to 1. Default: 1.
            x_page_size (int, optional): The number of records per page. Must be between 1 and 1000. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of students in the boarding dorm.

        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding/dorms/{internal_dorm_id}/students"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_boarding_dorm_students(self, id=None, internal_dorm_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of boarding dorm students.

        Args:
            id (int, optional): The ID of the boarding dorm student.
            internal_dorm_id (int, optional): The ID of the internal dorm.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of boarding dorm students.
        """
        if 'boarding.dorms.students:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'boarding.dorms.students:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding/dorms/{internal_dorm_id}/students"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'id': id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_boarding_dorm_students(self, internal_dorm_id, id, data):
        """
        Update the students in a boarding dorm.

        Args:
            internal_dorm_id (str): The internal ID of the dorm.
            id (str): The ID of the boarding dorm student.
            data (dict): The data to update the student in the boarding dorm. Should include the following fields:
                - room_number (str): The room number of the student.
                - floor_number (int): The floor number of the student.
                - bed_number (int): The bed number of the student.
                - currently_enrolled (bool): Whether the student is currently enrolled in the dorm.
                - late_date_enrolled (str): The date the student was enrolled in the dorm. Format: "YYYY-MM-DD".
                - date_withdrawn (str): The date the student was withdrawn from the dorm. Format: "YYYY-MM-DD".
                - notes (str): Any additional notes about the student.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated boarding dorm student information.

        """
        if 'update_boarding_dorm_students' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'update_boarding_dorm_students' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding_dorms/{internal_dorm_id}/students/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-API-Revision': 'string'
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                return pd.DataFrame([response.json()])
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_boarding_dorms(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        List boarding dorms.

        Args:
            on_or_after_last_modified_date (str, optional): Return dorms that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Return dorms that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            school_year (int, optional): Return dorms from the specified school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of boarding dorms.
        """

        if 'boarding.dorms:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'boarding.dorms:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "boarding/dorms"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_boarding_dorms(self, id):
        """
        Get a specific boarding dorm.

        Args:
            id (int): The internal ID of the dorm.

        Returns:
            pandas.DataFrame: A DataFrame containing the specific boarding dorm.
        """
        if 'Read Boarding: Dorms' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Boarding: Dorms' to your scopes.")
            return pd.DataFrame()

        endpoint = f"boarding/dorms/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': "string",
            'X-API-Value-Lists': "include"
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_class_attendance(self, id, internal_class_id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the class attendance for a specific class.

        Args:
            id (int): The ID of the attendance.
            internal_class_id (int): The internal ID of the class.

        Returns:
            pandas.DataFrame: A DataFrame containing the class attendance.

        """
        if 'read_class_attendance' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'read_class_attendance' to your scopes.")
            return pd.DataFrame()

        endpoint = f"read_class_attendance/{id}/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_class_attendance(self, internal_class_id, id, attendance_date, status, notes, x_api_revision):
        """
        Update the attendance for a specific class.

        Args:
            internal_class_id (str): The internal ID of the class.
            id (str): The attendance ID.
            attendance_date (str): The date of the attendance. Format: "YYYY-MM-DD".
            status (int): The status of the attendance.
            notes (str): Additional notes for the attendance.
            x_api_revision (str): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated attendance details.

        """
        if 'classes.attendance:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'classes.attendance:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"classes/{internal_class_id}/attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        params = {}

        body_data = {
            'attendance_date': attendance_date,
            'block': {
                'status': status,
                'notes': notes
            }
        }

        try:
            return self.fetch_data_from_api(endpoint, headers, params, method='PATCH', json=body_data)
        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_classes(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, primary_teacher_id=None, room_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of academic classes.

        Args:
            on_or_after_last_modified_date (str, optional): Only return classes that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return classes that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            primary_teacher_id (int, optional): Only return classes taught by the specified primary teacher ID.
            room_id (int, optional): Only return classes taught in the specified room ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of academic classes.

        """
        if 'classes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_class(self, id):
        """
        Get the details of a specific class.

        Args:
            id (int): The ID of the class to retrieve.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the class.
        """
        if 'classes:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'classes:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None,
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_contact_info(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of contact info.

        Args:
            on_or_after_last_modified_date (str, optional): Only return contact info that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return contact info that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            role (str, optional): Only return contact info with the specified role.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of contact info.

        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_contact_info"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_contact_info(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get contact information for a specific person.

        Args:
            id (int): The ID of the person.

        Returns:
            pandas.DataFrame: A DataFrame containing the contact information for the person.

        """
        if 'contact_info:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'contact_info:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"contact_info/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_courses(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of courses.

        Args:
            on_or_after_last_modified_date (str, optional): Only return courses that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return courses that were last modified on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of courses.

        """
        if 'courses:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'courses:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_courses(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a specific course.

        Args:
            id (int): The internal ID of the course.
            x_api_revision (str, optional): API Revision header.
            x_api_value_lists (str, optional): Include Value Lists in response header.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the course.
        """
        if 'courses:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'courses:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_course(self, id, name=None, course_type=None, course_id=None, catalog_title=None, catalog_description=None,
                      subject_description=None, department_id=None, department_description=None, x_api_revision=None):
        """
        Update a course.

        Args:
            id (int): The ID of the course to be updated.
            name (str, optional): The name of the course.
            course_type (int, optional): The type of the course.
            course_id (str, optional): The ID of the course.
            catalog_title (str, optional): The title of the course in the catalog.
            catalog_description (str, optional): The description of the course in the catalog.
            subject_description (str, optional): The description of the subject.
            department_id (int, optional): The ID of the department.
            department_description (str, optional): The description of the department.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated course.

        """
        if 'update_course' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'update_course' to your scopes.")
            return pd.DataFrame()

        endpoint = f"courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'name': name,
            'course_type': course_type,
            'course_id': course_id,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description,
            'subject': {'description': subject_description},
            'department': {'id': department_id, 'description': department_description}
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, method='PATCH')
            updated_course = response.get('data', {})
            df = pd.DataFrame([updated_course])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_directory_preferences_household(self, directory_type=None, household_id=None, household_name=None, status=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of directory preferences for a household.

        Args:
            directory_type (int, optional): The type of the directory.
            household_id (int, optional): The ID of the household.
            household_name (str, optional): The name of the household.
            status (int, optional): The status of the directory preferences.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of directory preferences for the household.

        """
        if 'directory.preferences.household:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'directory.preferences.household:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "directory/preferences/household"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'directory_type': directory_type,
            'household_id': household_id,
            'household_name': household_name,
            'status': status
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_directory_preferences_household(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Read the directory preferences for a household.

        Args:
            id (int): The ID of the household.
            x_api_revision (str, optional): The X-API-Revision header value.
            x_api_value_lists (str, optional): The X-API-Value-Lists header value.

        Returns:
            pandas.DataFrame: A DataFrame containing the directory preferences for the household.

        """
        if 'Read Directory Preferences: Household' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Read Directory Preferences: Household' to your scopes.")
            return pd.DataFrame()

        endpoint = f"directory/preferences/household/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_directory_preferences_household(self, id, data, x_api_revision=None):
        """
        Update the directory preferences for a household.

        Args:
            id (int): The ID of the household directory type preference.
            data (dict): The updated data for the household.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated directory preferences for the household.
        """
        if 'directory.preferences.household:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'directory.preferences.household:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"directory/preferences/household/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, params=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_directory_preferences_person(self, directory_type=None, person_id=None, person_name=None, status=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of directory preferences for a person.

        Args:
            directory_type (int, optional): The directory type.
            person_id (int, optional): The ID of the person.
            person_name (str, optional): The name of the person.
            status (int, optional): The status of the directory preference.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of directory preferences for the person.
        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_directory_preferences_person"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'directory_type': directory_type,
            'person_id': person_id,
            'person_name': person_name,
            'status': status
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_directory_preferences_person(self, id, data, x_api_revision=None):
        """

        Update the directory preferences for a person.



        Args:

            id (int): The ID of the person to update.

            data (dict): The data object containing the directory preferences to update. It should include the following optional fields: 

                - person_id (int): The ID of the person.

                - directory_type (int): The directory type.

                - status (int): The status.

                - parents_display (int): The display option for parents.

                - photo_display (int): The display option for photos.

                - mobile_phone_display (int): The display option for mobile phones.

                - email_1_display (int): The display option for email 1.

                - email_2_display (int): The display option for email 2.

                - business_phone_display (int): The display option for business phones.

            x_api_revision (str, optional): The API revision.



        Returns:

            pandas.DataFrame: A DataFrame containing the updated directory preferences for the person.

        """

        if 'directory.preferences.people:update' not in self.scopes:

            print("Error: You don't have the required scope for this endpoint. Please add 'directory.preferences.people:update' to your scopes.")

            return pd.DataFrame()

        endpoint = f"directory/preferences/people/{id}"

        headers = {

            'Authorization': f'Bearer {self.access_token}',

            'X-API-Revision': x_api_revision

        }

        try:

            self.fetch_data_from_api(endpoint, headers, {})

            print("Directory preferences updated successfully.")

            return pd.DataFrame()

        except Exception as e:

            print(f"Error: {str(e)}")

            return pd.DataFrame()

    def get_directory_type_configurations(self, category=None, configuration=None, directory_type=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of directory type configurations.

        Args:
            category (str, optional): The category of the configuration.
            configuration (str, optional): The specific configuration.
            directory_type (int, optional): The directory type.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of directory type configurations.

        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "directory_type_configurations"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'category': category,
            'configuration': configuration,
            'directory_type': directory_type
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_emergency_contacts(self, person_id, student_id, first_name, last_name, relationship, country, last_modified_date=None, middle_name=None, nick_name=None, legal_custody=None, pick_up=None, medical_notification=None, email_1=None, email_2=None, home_phone=None, mobile_phone=None, business_phone=None, address_1=None, address_2=None, city=None, state_province=None, postal_code=None, notes=None):
        """
        Create emergency contacts.

        Args:
            person_id (int): Person ID.
            student_id (int): Student ID.
            first_name (str): First Name.
            last_name (str): Last Name.
            relationship (int): Relationship.
            country (int): Country.
            last_modified_date (str, optional): Last Modified Date.
            middle_name (str, optional): Middle Name.
            nick_name (str, optional): Nick Name.
            legal_custody (bool, optional): Legal Custody.
            pick_up (bool, optional): Pick Up.
            medical_notification (bool, optional): Medical Notification.
            email_1 (str, optional): Email 1.
            email_2 (str, optional): Email 2.
            home_phone (str, optional): Home Phone.
            mobile_phone (str, optional): Mobile Phone.
            business_phone (str, optional): Business Phone.
            address_1 (str, optional): Address 1.
            address_2 (str, optional): Address 2.
            city (str, optional): City.
            state_province (str, optional): State Province.
            postal_code (str, optional): Postal Code.
            notes (str, optional): Notes.

        Returns:
            pandas.DataFrame: A DataFrame containing the created emergency contacts.
        """
        if 'emergency_contacts:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'emergency_contacts:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "emergency_contacts"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'API Revision'
        }
        data = {
            'person_id': person_id,
            'student_id': student_id,
            'first_name': first_name,
            'last_name': last_name,
            'relationship': relationship,
            'country': country,
            'last_modified_date': last_modified_date,
            'middle_name': middle_name,
            'nick_name': nick_name,
            'legal_custody': legal_custody,
            'pick_up': pick_up,
            'medical_notification': medical_notification,
            'email_1': email_1,
            'email_2': email_2,
            'home_phone': home_phone,
            'mobile_phone': mobile_phone,
            'business_phone': business_phone,
            'address_1': address_1,
            'address_2': address_2,
            'city': city,
            'state_province': state_province,
            'postal_code': postal_code,
            'notes': notes
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def delete_emergency_contact(self, id, x_api_revision=None):
        """
        Delete an emergency contact.

        Args:
            id (int): The ID of the person whose emergency contact needs to be deleted.

        Returns:
            pandas.DataFrame: A DataFrame containing the response from the API after deleting the emergency contact.

        """
        if 'emergency_contacts:delete' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'emergency_contacts:delete' to your scopes.")
            return pd.DataFrame()

        endpoint = f"emergency_contacts/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint}", headers=headers)
            if response.status_code == 204:
                print("Emergency contact deleted successfully.")
            else:
                print(f"Error: {response.status_code} - {response.text}")
            return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_emergency_contact(self, id, data):
        """
        Update an emergency contact.

        Args:
            id (int): The ID of the emergency contact to be updated.
            data (dict): The data to be updated. It should include the following fields:
                - person_id (int): The ID of the person.
                - student_id (int): The ID of the student.
                - first_name (str): The first name of the contact.
                - middle_name (str): The middle name of the contact.
                - last_name (str): The last name of the contact.
                - nick_name (str): The nickname of the contact.
                - relationship (int): The ID of the relationship.
                - legal_custody (bool): True if the contact has legal custody, False otherwise.
                - pick_up (bool): True if the contact can pick up the student, False otherwise.
                - medical_notification (bool): True if the contact should receive medical notifications, False otherwise.
                - email_1 (str): The first email address of the contact.
                - email_2 (str): The second email address of the contact.
                - home_phone (str): The home phone number of the contact.
                - mobile_phone (str): The mobile phone number of the contact.
                - business_phone (str): The business phone number of the contact.
                - address_1 (str): The first line of the contact's address.
                - address_2 (str): The second line of the contact's address.
                - city (str): The city of the contact's address.
                - state_province (str): The state or province of the contact's address.
                - postal_code (str): The postal code of the contact's address.
                - country (int): The ID of the country.
                - notes (str): Additional notes about the contact.
                - last_modified_date (str): The last modified date of the contact. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the updated emergency contact.

        """
        if 'emergency_contacts:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'emergency_contacts:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"emergency_contacts/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                contact_data = response.json()
                df = pd.DataFrame(contact_data)
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_event(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a specific event.

        Args:
            id (int): The ID of the event.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include Value Lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the event.
        """
        if 'events.group_events:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'events.group_events:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"events/group_events/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_events_athletics(self, event_type=None, internal_team_id=None, on_or_after_start_date=None, on_or_after_update_date=None, on_or_before_end_date=None, on_or_before_update_date=None, public=None, school_level=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of athletics events.

        Args:
            event_type (int, optional): The ID of the event type.
            internal_team_id (int, optional): The ID of the internal group.
            on_or_after_start_date (str, optional): Only return events that start on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_update_date (str, optional): Only return events that were last updated on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_end_date (str, optional): Only return events that end on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_update_date (str, optional): Only return events that were last updated on or before this specific date. Format: "YYYY-MM-DD".
            public (bool, optional): Whether to display the event on the public calendar.
            school_level (int, optional): The ID of the school level.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Whether to include value lists in the response.
            x_page_number (int, optional): The page number. Default is 1.
            x_page_size (int, optional): The number of records per page. Minimum is 1, maximum is 100. Default is 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of athletics events.

        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_events_athletics"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'event_type': event_type,
            'internal_team_id': internal_team_id,
            'on_or_after_start_date': on_or_after_start_date,
            'on_or_after_update_date': on_or_after_update_date,
            'on_or_before_end_date': on_or_before_end_date,
            'on_or_before_update_date': on_or_before_update_date,
            'public': public,
            'school_level': school_level
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_events_athletics(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of an athletics event.

        Args:
            id (int): The ID of the athletics event.
            x_api_revision (str, optional): The revision number of the API.
            x_api_value_lists (str, optional): The value lists required for the API.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the athletics event.
        """
        if 'events.athletics:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'events.athletics:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"events/athletics/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_class_attendance(self, internal_class_id, on_or_after_attendance_date=None, on_or_after_last_modified_date=None, on_or_before_attendance_date=None, on_or_before_last_modified_date=None, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of extended care class attendance.

        Args:
            internal_class_id (int): The ID of the internal class.
            on_or_after_attendance_date (str, optional): Only return attendance records on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return attendance records that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_attendance_date (str, optional): Only return attendance records on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return attendance records that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): Only return attendance records for the specified person ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of extended care class attendance.

        """
        if 'extended_care.class_attendance:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care.class_attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended-care-classes/{internal_class_id}/attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_attendance_date': on_or_after_attendance_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_attendance_date': on_or_before_attendance_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_class_attendance(self, internal_class_id, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get extended care class attendance.

        Args:
            internal_class_id (int): The internal ID of the class.
            id (int): The ID of the attendance record.
            x_api_revision (str, optional): The API revision version.
            x_api_value_lists (str, optional): The value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the extended care class attendance.
        """
        if 'extended_care.classes.attendance:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care.classes.attendance:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended_care/class/{internal_class_id}/attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params={})
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_class_meeting_times(self, internal_class_id, day=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of extended care class meeting times.

        Args:
            internal_class_id (int): The internal class ID.
            day (str, optional): The description of the day.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of extended care class meeting times.

        """
        if 'extended_care.class_meeting_times:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'extended_care.class_meeting_times:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended-care/class-meeting-times/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'day': day
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def extended_care_class_meeting_times(self, internal_class_id, id, x_api_revision: str, x_api_value_lists: str):
        """
        Get the meeting times for an extended care class.

        Args:
            internal_class_id (str): The internal ID of the class.
            id (str): The ID of the extended care class.
            x_api_revision (str): The API revision value.
            x_api_value_lists (str): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the meeting times for the extended care class.
        """
        if 'extended_care.classes.meeting_times:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care.classes.meeting_times:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended-care/classes/{internal_class_id}/meeting-times/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_extended_care_classes(self, internal_course_id, class_id, description, status, school_year, begin_date, end_date, primary_grade_level_id, school_level_id, primary_teacher_id, room_id, virtual_meeting_url, x_api_revision=None):
        """
        Create extended care classes.

        Args:
            internal_course_id (int): Course ID (Internal).
            class_id (str): Class ID.
            description (str): Description.
            status (int): Status.
            school_year (int): School Year.
            begin_date (str): Begin Date.
            end_date (str): End Date.
            primary_grade_level_id (int): Primary Grade Level ID.
            school_level_id (int): School Level.
            primary_teacher_id (int): Teacher ID.
            room_id (int): Room ID.
            virtual_meeting_url (str): Virtual Meeting URL.
            x_api_revision (str, optional): API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the created extended care classes.
        """
        if 'extendedcare.classes:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'extendedcare.classes:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "extended_care/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'internal_course_id': internal_course_id,
            'class_id': class_id,
            'description': description,
            'status': status,
            'school_year': school_year,
            'begin_date': begin_date,
            'end_date': end_date,
            'primary_grade_level_id': primary_grade_level_id,
            'school_level_id': school_level_id,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'virtual_meeting_url': virtual_meeting_url
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_classes(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the extended care classes.

        Args:
            id (int, required): The internal class ID.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.

        Returns:
            pandas.DataFrame: A DataFrame containing the extended care classes.

        """
        if 'Read Extended Care: Classes' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Extended Care: Classes' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended_care_classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_extended_care_classes(self, id, data, x_api_revision=None):
        """
        Update extended care classes.

        Args:
            id (int): Internal Class ID.
            data (dict): Data to update the extended care class.
            x_api_revision (str, optional): API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated extended care class.
        """
        if 'extended_care.classes:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care.classes:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended_care/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, call_type='PATCH')
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_courses(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of extended care courses.

        Args:
            on_or_after_last_modified_date (str, optional): Only return courses that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return courses that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response. Allowed value: "include".
            x_page_number (int, optional): Page number. Default: 1.
            x_page_size (int, optional): Number of records per page. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of extended care courses.

        """
        endpoint = "extendedcare/courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_extended_care_courses(self, name, subject_id, course_id, catalog_title, catalog_description):
        """
        Create extended care courses.

        Args:
            name (str): The name of the course.
            subject_id (str): The ID of the subject.
            course_id (str): The ID of the course.
            catalog_title (str): The title of the course in the catalog.
            catalog_description (str): The description of the course in the catalog.

        Returns:
            pandas.DataFrame: A DataFrame containing the created extended care courses.

        """
        if 'extended_care.courses:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care.courses:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "extended-care/courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-API-Revision': ''
        }
        data = {
            'name': name,
            'subject_id': subject_id,
            'course_id': course_id,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description
        }

        try:
            response = self.execute_api_request(
                endpoint, headers, data, method='POST')
            df = pd.DataFrame(response.json().get('data', []))
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_course(self, id=None, name=None, subject_id=None, subject_description=None, course_id=None, catalog_title=None, catalog_description=None, last_modified_date=None, value_lists=None):
        """
        Get the details of an extended care course.

        Args:
            id (int, required): Internal Course ID.
            name (str, required): Course Name.
            subject_id (int, required): Subject ID.
            subject_description (str, required): Description of the subject.
            course_id (str, required): Course ID.
            catalog_title (str, required): Catalog Title.
            catalog_description (str, required): Catalog Description.
            last_modified_date (str, required): Last Modified Date. Format: "YYYY-MM-DD".
            value_lists (list, optional): A list of value lists. Present only with header X-API-Value-Lists=include.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the extended care course.
        """
        if 'extended_care_course:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care_course:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended_care_course/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_extended_care_course(self, id, name, subject_id, subject_description, course_id, catalog_title, catalog_description, x_api_revision=None):
        """
        Update an extended care course.

        Args:
            id (int): The ID of the extended care course to be updated.
            name (str): The name of the extended care course.
            subject_id (int): The ID of the subject associated with the extended care course.
            subject_description (str): The description of the subject associated with the extended care course.
            course_id (str): The ID of the course.
            catalog_title (str): The title of the course in the catalog.
            catalog_description (str): The description of the course in the catalog.
            x_api_revision (str, optional): The revision of the API.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated extended care course.

        """
        if 'extended_care.courses:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'extended_care.courses:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended-care/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        body = {
            'name': name,
            'subject_id': subject_id,
            'subject_description': subject_description,
            'course_id': course_id,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params=body)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_registrations(self, internal_class_id=None, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of extended care registrations.

        Args:
            internal_class_id (int, optional): Internal Class ID.
            person_id (int, optional): Person ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of extended care registrations.
        """
        if 'extended_care_registrations:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'extended_care_registrations:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "extended_care_registrations"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id,
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_registration(self, id):
        """
        Get information about an extended care registration.

        Args:
            id (int): The ID of the extended care registration.

        Returns:
            pandas.DataFrame: A DataFrame containing the information about the extended care registration.

        """
        if 'extended_care.registrations:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'extended_care.registrations:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"extended_care/registrations/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_health_patient_conditions(self, patient_id, critical=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of health conditions for a patient.

        Args:
            patient_id (int): The ID of the patient.
            critical (bool, optional): Whether to only return critical conditions.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of health conditions for the patient.

        """
        if 'health.patient.conditions:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'health.patient.conditions:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patient/{patient_id}/conditions"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'critical': critical
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_patient_condition(self, patient_id, data):
        """
        Create a new patient condition.

        Args:
            patient_id (str): The ID of the patient.
            data (dict): The data for the new patient condition.
                - description (str): [Required] Description.
                - condition_code (int): [Required] Condition Code.
                - new_condition_code_description (str): [Required] Condition Code Description.
                - intervention_code (int): [Required] Intervention Code.
                - new_intervention_code_description (str): [Required] Intervention Code Description.
                - begin_date (str): Begin Date.
                - end_date (str): End Date.
                - notes (str): Notes.
                - critical (bool): [Required] Critical.

        Returns:
            pandas.DataFrame: A DataFrame containing the new patient condition.

        """
        if 'health.patients.conditions:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'health.patients.conditions:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{patient_id}/conditions"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.post_data_to_api(endpoint, headers, data)
            df = pd.DataFrame(response.json())

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_health_patient_conditions(self, patient_id, id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of conditions for a specific patient.

        Args:
            patient_id (int): The ID of the patient.
            id (int): The ID of the condition.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of conditions for the patient.
        """

        if 'Health' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Health' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{patient_id}/conditions/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_health_patient_condition(self, patient_id, id, description, condition_code, intervention_code, begin_date, end_date, notes, critical):
        """
        Update a patient's health condition.

        Args:
            patient_id (str): The ID of the patient.
            id (str): The ID of the condition.
            description (str): The description of the condition.
            condition_code (int): The condition code.
            intervention_code (int): The intervention code.
            begin_date (str): The begin date of the condition. Format: "YYYY-MM-DD".
            end_date (str): The end date of the condition. Format: "YYYY-MM-DD".
            notes (str): Any notes related to the condition.
            critical (bool): Specifies if the condition is critical or not.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated condition details.

        """
        if 'health.patients.conditions:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'health.patients.conditions:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{patient_id}/conditions/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }
        body_data = {
            'description': description,
            'condition_code': condition_code,
            'intervention_code': intervention_code,
            'begin_date': begin_date,
            'end_date': end_date,
            'notes': notes,
            'critical': critical
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, body_data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_health_patient_medications(self, patient_id, medication, start_date, end_date, dosage_instruction, notes, x_api_revision):
        """
        Create a new health patient medication record.

        Args:
            patient_id (int): The ID of the patient.
            medication (int): The ID of the medication.
            start_date (str): The start date of the medication. Format: "YYYY-MM-DD".
            end_date (str): The end date of the medication. Format: "YYYY-MM-DD".
            dosage_instruction (str): The dosage instruction for the medication.
            notes (str): Additional notes for the medication.
            x_api_revision (str): The API revision value.

        Returns:
            pandas.DataFrame: A DataFrame containing the created health patient medication record.

        """
        endpoint = f"health/patients/{patient_id}/medications"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            "data": {
                "patient_id": patient_id,
                "medication": medication,
                "start_date": start_date,
                "end_date": end_date,
                "dosage_instruction": dosage_instruction,
                "notes": notes
            }
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, method='POST')
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_patient_medications(self, patient_id, medication=None, on_or_after_start_date=None, on_or_before_start_date=None, on_or_after_end_date=None, on_or_before_end_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of medications for a specific patient.

        Args:
            patient_id (int): The ID of the patient.
            medication (int, optional): The ID of the medication.
            on_or_after_start_date (str, optional): Only return medications that start on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_start_date (str, optional): Only return medications that start on or before this specific date. Format: "YYYY-MM-DD".
            on_or_after_end_date (str, optional): Only return medications that end on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_end_date (str, optional): Only return medications that end on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of medications for the patient.

        """
        if 'health.patients.medications:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'health.patients.medications:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{patient_id}/medications"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'medication': medication,
            'on_or_after_start_date': on_or_after_start_date,
            'on_or_before_start_date': on_or_before_start_date,
            'on_or_after_end_date': on_or_after_end_date,
            'on_or_before_end_date': on_or_before_end_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_patient_medication(self, id=None, patient_id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a patient's medication.

        Args:
            id (int, required): The ID of the medication.
            patient_id (int, required): The ID of the patient.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the patient's medication.

        """
        if 'Health: Patient Medications' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Health: Patient Medications' to your scopes.")
            return pd.DataFrame()

        endpoint = f"read_patient_medication/{id}/{patient_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_patient_medication(self, patient_id, id, data):
        """
        Update a patient's medication.

        Args:
            patient_id (int): The ID of the patient.
            id (int): The ID of the medication.
            data (dict): The updated information for the medication.
                - patient_id (int): The ID of the patient.
                - medication (int): The ID of the medication.
                - start_date (str): The start date of the medication. Format: "YYYY-MM-DD".
                - end_date (str): The end date of the medication. Format: "YYYY-MM-DD".
                - dosage_instruction (str): The dosage instructions for the medication.
                - notes (str): Additional notes for the medication.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated patient's medication information.

        """
        if 'health.patients.medications:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'health.patients.medications:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{patient_id}/medications/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, request_type='PATCH')

            return pd.DataFrame(response)

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_health_patients(self, name=None, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of health patients.

        Args:
            name (str, optional): The name of the patient.
            role (str, optional): The role of the patient.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of health patients.

        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_health_patients"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'name': name,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_health_patients(self, id):
        """
        Get information about a specific health patient.

        Args:
            id (int): The ID of the health patient.

        Returns:
            pandas.DataFrame: A DataFrame containing the information about the health patient.
        """
        if 'health.patients:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'health.patients:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"health/patients/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_health_patients(self, id, data, x_api_revision=None):
        """
        Update the health information of a patient.

        Args:
            id (int): The ID of the person.
            data (dict): The updated health information of the patient.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated health information of the patient.

        """
        if 'update_health_patients:patch' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'update_health_patients:patch' to your scopes.")
            return pd.DataFrame()

        endpoint = f"update_health_patients/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)

            if response.status_code == 200:
                df = pd.DataFrame(response.json().get('data', []))
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_households(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of households.

        Args:
            on_or_after_last_modified_date (str, optional): Only return households that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return households that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include this parameter to get value lists for fields.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination. Must be between 1 and 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of households.
        """
        if 'households:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'households:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "households"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_households(self, id):
        """
        Get information about a specific household.

        Args:
            id (int): The ID of the household.

        Returns:
            pandas.DataFrame: A DataFrame containing the information about the household.
        """
        if 'read_households' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'read_households' to your scopes.")
            return pd.DataFrame()

        endpoint = "households/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': '',
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_master_attendance(self, attendance_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of master attendance.

        Args:
            attendance_date (str, optional): Attendance date in format "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return master attendance that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return master attendance that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): Only return master attendance for the specified person ID.
            x_api_revision (str, optional): API revision.
            x_api_value_lists (str, optional): Include value lists in response. Allowed value: "include".
            x_page_number (int, optional): Page number. Default: 1.
            x_page_size (int, optional): Number of records per page. Must be between 1 and 100. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of master attendance.
        """
        if 'master_attendance:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'master_attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "master_attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'attendance_date': attendance_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")

        return pd.DataFrame()

    def get_master_attendance(self, id):
        """
        Retrieve the master attendance record for a specific ID.

        Args:
            id (int): The ID of the master attendance record.

        Returns:
            pandas.DataFrame: A DataFrame containing the master attendance record.
        """
        if 'master_attendance:id' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'master_attendance:id' to your scopes.")
            return pd.DataFrame()

        endpoint = f"master_attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'X-API-Revision': '',
            'X-API-Value-Lists': '',
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_master_attendance(self, id, data, x_api_revision=None):
        """
        Update the master attendance.

        Args:
            id (int): Daily Attendance ID.
            data (dict): Attendance data.
            x_api_revision (str, optional): API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated master attendance.
        """

        if 'master_attendance:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'master_attendance:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"master_attendance/{id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-API-Revision": x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data=data, call_type="PATCH")
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_parents(self, household_id=None, include_deceased=None, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of parents.

        Args:
            household_id (int, optional): The ID of the household.
            include_deceased (bool, optional): Flag to include deceased parents.
            role (str, optional): The role of the parent.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of parents.
        """
        if 'parents:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'parents:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "parents"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'household_id': household_id,
            'include_deceased': include_deceased,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_parent(self, id):
        """
        Get the information of a parent.

        Args:
            id (int): The ID of the parent.

        Returns:
            pandas.DataFrame: A DataFrame containing the information of the parent.
        """
        if 'parents:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'parents:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"parents/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': None,
            'X-API-Value-Lists': None,
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_class_attendance(self, internal_class_id, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of program class attendance.

        Args:
            internal_class_id (str): The internal ID of the class.
            person_id (int, optional): The ID of the person whose attendance is being queried.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): The value lists to include in the response.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The number of items per page for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of program class attendance.

        """
        if 'programs.class_attendance:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.class_attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/class_attendance/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_class_attendance(self, id=None, internal_class_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the programs class attendance.

        Args:
            id (int, required): The ID of the program class attendance.
            internal_class_id (int, required): The internal ID of the class.

        Returns:
            pandas.DataFrame: A DataFrame containing the programs class attendance data.
        """
        if 'programs.classes.attendance:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'programs.classes.attendance:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/classes/{id}/attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_programs_class_attendance(self, internal_class_id, id, data):
        """
        Update the attendance for a class in the programs module.

        Args:
            internal_class_id (int): The internal ID of the class.
            id (int): The ID of the attendance record.
            data (dict): The data to be updated.
                - attendance_date (str): The date of the attendance.
                - block (dict): The block information.
                - status (int): The attendance status.
                - notes (str): Additional notes for the attendance.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated attendance record for the class.
        """
        if 'programs.class_attendance:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.class_attendance:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/classes/{internal_class_id}/attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, method='PATCH', data=data)
            if response.status_code == 200:
                attendance = response.json()
                df = pd.DataFrame([attendance])
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_class_meeting_times(self, internal_class_id, X_Page_Number=1, X_Page_Size=1000, X_API_Revision=None, X_API_Value_Lists=None):
        """
        Get the list of meeting times for a specific class in a program.

        Args:
            internal_class_id (int): The ID of the internal class.
            X_Page_Number (int, optional): The page number to retrieve. Default is 1.
            X_Page_Size (int, optional): The number of items per page. Default is 1000.
            X_API_Revision (str, optional): The API revision.
            X_API_Value_Lists (str, optional): The value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of meeting times for the class.

        """
        if 'programs.classes.meeting_times:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.classes.meeting_times:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/classes/{internal_class_id}/meeting_times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': X_API_Revision,
            'X-API-Value-Lists': X_API_Value_Lists,
            'X-Page-Number': str(X_Page_Number),
            'X-Page-Size': str(X_Page_Size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_class_meeting_times(self, id, internal_class_id, date=None, start_time=None, end_time=None, grading_period=None, day=None, block=None, room=None, value_lists=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the class meeting times for a specific program.

        Args:
            id (int): The ID of the program.
            internal_class_id (int): The internal ID of the class.
            date (str, optional): The date of the meeting time. Format: "YYYY-MM-DD".
            start_time (str, optional): The start time of the meeting time. Format: "HH:MM".
            end_time (str, optional): The end time of the meeting time. Format: "HH:MM".
            grading_period (dict, optional): The grading period information.
            day (dict, optional): The day information.
            block (dict, optional): The block information.
            room (dict, optional): The room information.
            value_lists (list, optional): An array of objects for value lists.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value lists string for API.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the class meeting times.

        """
        if 'read_programs_class_meeting_times' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'read_programs_class_meeting_times' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/{id}/class-meeting-times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'grading_period': grading_period,
            'day': day,
            'block': block,
            'room': room,
            'value_lists': value_lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_program_class(self, class_id, description, status, school_year, begin_date, end_date, primary_grade_level_id, internal_course_id, primary_teacher_id, room_id, virtual_meeting_url):
        """
        Create a program class.

        Args:
            class_id (str): The ID of the class.
            description (str): The description of the class.
            status (int): The status of the class.
            school_year (int): The school year of the class.
            begin_date (str): The begin date of the class. Format: "YYYY-MM-DD".
            end_date (str): The end date of the class. Format: "YYYY-MM-DD".
            primary_grade_level_id (int): The primary grade level ID of the class.
            internal_course_id (int): The internal course ID of the class.
            primary_teacher_id (int): The primary teacher ID of the class.
            room_id (int): The room ID of the class.
            virtual_meeting_url (str): The virtual meeting URL of the class.

        Returns:
            pandas.DataFrame: A DataFrame containing the created program class information.

        """

        if 'programs.classes:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'programs.classes:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "programs/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Revision': 'string'
        }

        body_data = {
            "class_id": class_id,
            "description": description,
            "status": status,
            "school_year": school_year,
            "begin_date": begin_date,
            "end_date": end_date,
            "primary_grade_level_id": primary_grade_level_id,
            "internal_course_id": internal_course_id,
            "primary_teacher_id": primary_teacher_id,
            "room_id": room_id,
            "virtual_meeting_url": virtual_meeting_url
        }

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, json=body_data)

            if response.status_code == 200:
                data = response.json().get('data', {})
                df = pd.DataFrame(data)
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_program_classes(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, primary_teacher_id=None, room_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of program classes.

        Args:
            on_or_after_last_modified_date (str, optional): Only return classes that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return classes that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            primary_teacher_id (int, optional): Only return classes taught by the specified primary teacher ID.
            room_id (int, optional): Only return classes taught in the specified room ID.
            school_year (int, optional): Only return classes from the specified school year.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value lists for the API.
            x_page_number (int, optional): The page number for pagination. Default is 1.
            x_page_size (int, optional): The page size for pagination. Default is 1000.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of program classes.
        """
        if 'academics.classes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'academics.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "academics/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_class(self, id):
        """
        Get details of a specific program class.

        Args:
            id (int): The internal ID of the class.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the program class.
        """
        if 'programs.classes:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'programs.classes:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_programs_classes(self, id, x_api_revision=None, data=None):
        """
        Update a specific program class.

        Args:
            id (int): The internal Class ID of the program class to be updated.
            x_api_revision (str, optional): The API Revision.
            data (dict, optional): The data to be updated for the program class. Should include the following keys:
                                - class_id (str)
                                - description (str)
                                - status (int)
                                - school_year (int)
                                - begin_date (str)
                                - end_date (str)
                                - primary_grade_level_id (int)
                                - internal_course_id (int)
                                - primary_teacher_id (int)
                                - room_id (int)
                                - virtual_meeting_url (str)

        Returns:
            pandas.DataFrame: A DataFrame containing the updated program class.

        """
        if 'programs.classes:edit' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.classes:edit' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
        }
        params = {}

        try:
            response = self.send_data_to_api(endpoint, headers, params, data)
            if response.status_code == 200:
                updated_data = response.json().get('data', {})
                df = pd.DataFrame(updated_data, index=[0])
                return df
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_courses(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of programs courses.

        Args:
            on_or_after_last_modified_date (str, optional): Only return courses that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return courses that were last modified on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of programs courses.

        """
        if 'programs.courses:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.courses:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "programs/courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_programs_courses(self, school_route, data):
        """
        Create programs courses.

        Args:
            school_route (str): The route for the school.
            data (dict): The data for creating the programs courses.

        Returns:
            pandas.DataFrame: A DataFrame containing the created programs courses.
        """
        if 'create_programs_courses' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'create_programs_courses' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/courses/{school_route}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'API Revision'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_courses(self, id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the details of a specific course in a program.

        Args:
            id (int): The internal course ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the course in a program.
        """
        if 'programs.courses:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.courses:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params=None)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_programs_course(self, id, data, x_api_revision=None, auth_token=None):
        """
        Update a program's course.

        Args:
            id (int): Internal Course ID.
            data (dict): Data to update the course.
            - name (str): Course Name.
            - course_id (str): Course ID.
            - subject (dict):
                - catalog_title (str): Catalog Title.
                - catalog_description (str): Catalog Description.
            x_api_revision (str, optional): API Revision.
            auth_token (str, optional): Authorization Token.

        Returns:
            pandas.DataFrame: A DataFrame representing the updated program's course.

        """
        endpoint = f"programs/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        body_data = {
            'data': data
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, body_data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_enrollments(self, internal_class_id=None, person_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of program enrollments.

        Args:
            internal_class_id (int, optional): Filter enrollments by internal class ID.
            person_id (int, optional): Filter enrollments by person ID.
            school_year (int, optional): Filter enrollments by school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of program enrollments.

        """
        if 'programs.enrollments:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.enrollments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "programs/enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_programs_enrollments(self, id=None, data=None):
        """
        Get the enrollment details for a specific program.

        Args:
            id (int): The ID of the enrollment.
            data (dict): The data for the enrollment including enrollment ID, internal class ID, person ID, grade level ID, currently enrolled status, late date enrolled, date withdrawn, enrollment level, and notes.

        Returns:
            pandas.DataFrame: A DataFrame containing the enrollment details.

        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/enrollments/{id}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_programs_enrollment(self, id=None, currently_enrolled=None, late_date_enrolled=None, date_withdrawn=None, level=None, notes=None, x_api_revision=None, auth_token=None):
        """
        Update the enrollment details of a program.

        Args:
            id (int): The ID of the program enrollment to be updated.
            currently_enrolled (bool, optional): Indicates if the student is currently enrolled in the program.
            late_date_enrolled (str, optional): The date the student was enrolled late in the program. Format: "YYYY-MM-DD".
            date_withdrawn (str, optional): The date the student was withdrawn from the program. Format: "YYYY-MM-DD".
            level (int, optional): The level of the student in the program.
            notes (str, optional): Additional notes or comments about the program enrollment.
            x_api_revision (str): The API revision version.
            auth_token (str): The authorization token.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated program enrollment details.

        """
        if 'programs.enrollments:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.enrollments:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"programs/enrollments/{id}"
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'currently_enrolled': currently_enrolled,
            'late_date_enrolled': late_date_enrolled,
            'date_withdrawn': date_withdrawn,
            'level': level,
            'notes': notes
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_program_enrollment(self, internal_class_id, person_id, currently_enrolled=True, late_date_enrolled=None, date_withdrawn=None, level=None, notes=None):
        """
        Create a program enrollment.

        Args:
            internal_class_id (int): The internal class ID for the enrollment.
            person_id (int): The ID of the person for the enrollment.
            currently_enrolled (bool, optional): Whether the person is currently enrolled in the program. Default is True.
            late_date_enrolled (str, optional): The late date the person enrolled in the program. Format: "YYYY-MM-DD".
            date_withdrawn (str, optional): The date the person withdrew from the program. Format: "YYYY-MM-DD".
            level (int, optional): The enrollment level.
            notes (str, optional): Additional notes for the enrollment.

        Returns:
            pandas.DataFrame: A DataFrame containing the created program enrollment.

        """
        if 'programs.enrollments:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'programs.enrollments:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "programs/enrollments/"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '1',
        }
        data = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'currently_enrolled': currently_enrolled,
            'late_date_enrolled': late_date_enrolled,
            'date_withdrawn': date_withdrawn,
            'level': level,
            'notes': notes
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, json.dumps(data), method='POST')
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_relationships(self, emergency=None, legal_custody=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, person_id=None, pick_up=None, related_person_id=None, relationship=None, resident=None, role=None, X_API_Revision=None, X_API_Value_Lists=None, X_Page_Number=1, X_Page_Size=1000):
        """
        Get the list of relationships.

        Args:
            emergency (bool, optional): Filter by emergency relationships.
            legal_custody (bool, optional): Filter by relationships with legal custody.
            on_or_after_last_modified_date (str, optional): Only return relationships that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return relationships that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): Filter by the specified person ID.
            pick_up (bool, optional): Filter by relationships with pick up permission.
            related_person_id (int, optional): Filter by the specified related person ID.
            relationship (int, optional): Filter by the specified relationship ID.
            resident (bool, optional): Filter by relationships with resident permission.
            role (int, optional): Filter by the specified role ID.
            X_API_Revision (str, optional): The API revision header.
            X_API_Value_Lists (str, optional): The value lists header.
            X_Page_Number (int, optional): The page number for pagination.
            X_Page_Size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of relationships.

        """
        if 'relationships:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'relationships:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': X_API_Revision,
            'X-API-Value-Lists': X_API_Value_Lists,
            'X-Page-Number': str(X_Page_Number),
            'X-Page-Size': str(X_Page_Size)
        }
        params = {
            'emergency': emergency,
            'legal_custody': legal_custody,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id,
            'pick_up': pick_up,
            'related_person_id': related_person_id,
            'relationship': relationship,
            'resident': resident,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_relationships(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the relationships for a specific person.

        Args:
            id (int): The ID of the person.

        Returns:
            pandas.DataFrame: A DataFrame containing the relationships for the specified person.

        """
        endpoint = f"relationships/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_person_relationships(self, id, emergency=None, legal_custody=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, pick_up=None, relationship=None, resident=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of person relationships.

        Args:
            id (int): The ID of the person.
            emergency (bool, optional): Filter relationships by emergency flag.
            legal_custody (bool, optional): Filter relationships by legal custody flag.
            on_or_after_last_modified_date (str, optional): Filter relationships that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Filter relationships that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            pick_up (bool, optional): Filter relationships by pick up flag.
            relationship (int, optional): Filter relationships by relationship ID.
            resident (bool, optional): Filter relationships by resident flag.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value lists.
            x_page_number (int, optional): The page number for pagination. Default is 1.
            x_page_size (int, optional): The page size for pagination. Default is 1000.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of person relationships.

        """
        if 'people.relationships:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'people.relationships:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"people/{id}/relationships"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'emergency': emergency,
            'legal_custody': legal_custody,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'pick_up': pick_up,
            'relationship': relationship,
            'resident': resident
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_academic_classifications(self, person_id, grading_period=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of report card academic classifications for a person.

        Args:
            person_id (int): The ID of the person.
            grading_period (str, optional): The description or abbreviation of the grading period.
            school_year (str, optional): The description or abbreviation of the school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report card academic classifications for the person.

        """
        if 'list_report_card_academic_classifications' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'list_report_card_academic_classifications' to your scopes.")
            return pd.DataFrame()

        endpoint = f"list_report_card_academic_classifications/{person_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'grading_period': grading_period,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_academic_classifications(self, id, person_id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the academic classifications for a specific person in a report card.

        Args:
            id (int): The ID of the report card.
            person_id (int): The ID of the person.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the academic classifications.

        """
        if 'report_card.students.academic_classifications:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.students.academic_classifications:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/{id}/students/{person_id}/academic_classifications"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_class_curriculum(self, internal_class_id=None, enrollment_level_id=None, rubric_category_id=None, rubric_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of class curriculum for a specific internal class.

        Args:
            internal_class_id (int): The ID of the internal class.
            enrollment_level_id (int, optional): The ID of the enrollment level for filtering the curriculum.
            rubric_category_id (int, optional): The ID of the rubric category for filtering the curriculum.
            rubric_id (int, optional): The ID of the rubric for filtering the curriculum.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): The value lists for filtering the curriculum.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of class curriculum.

        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/classes/{internal_class_id}/curriculum"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'enrollment_level_id': enrollment_level_id,
            'rubric_category_id': rubric_category_id,
            'rubric_id': rubric_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_class_curriculum(self, id, internal_class_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the curriculum for a specific class in the report cards.

        Args:
            id (int): The ID of the report card.
            internal_class_id (int): The internal class ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the curriculum for the specified class in the report cards.

        """
        if 'report_card.classes.curriculum:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.classes.curriculum:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_cards/{id}/classes/{internal_class_id}/curriculum"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, None)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_class_teachers(self, internal_class_id, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        List report cards for class teachers.

        Args:
            internal_class_id (int): The internal class ID.
            role (int, optional): The role.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report cards for class teachers.
        """
        if 'report_card/class_teachers:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'report_card/class_teachers:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/class_teachers/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_class_teachers(self, id=None, internal_class_id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the list of report card class teachers.

        Args:
            id (int, optional): The ID of the report card.
            internal_class_id (int, optional): The ID of the internal class.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report card class teachers.
        """
        if 'report_card.classes.teachers:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.classes.teachers:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/classes/{id}/teachers/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_documents(self, id):
        """
        Get the academic document for a person.

        Args:
            id (int): Person Academic Document ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the academic document.

        """
        if 'report_card.documents:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.documents:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/documents/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_documents(self, academic_document_id=None, grading_period_id=None, person_id=None, school_year_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of report card documents.

        Args:
            academic_document_id (int, optional): The ID of the academic document.
            grading_period_id (int, optional): The ID of the grading period.
            person_id (int, optional): The ID of the person.
            school_year_id (int, optional): The ID of the school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report card documents.

        """
        if 'report_card.documents:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.documents:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "report_card/documents"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'academic_document_id': academic_document_id,
            'grading_period_id': grading_period_id,
            'person_id': person_id,
            'school_year_id': school_year_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_enrollments(self, course_classification=None, course_type=None, person_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000, data=[]):
        """
        Get the list of report card enrollments.

        Args:
            course_classification (str, optional): The classification of the course.
            course_type (str, optional): The type of the course.
            person_id (int, required): The ID of the person.
            school_year (int, required): The school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report card enrollments.

        """
        if 'report_card_enrollments:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'report_card_enrollments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "report_card_enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'course_classification': course_classification,
            'course_type': course_type,
            'person_id': person_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_enrollments(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Read the report card enrollments.

        Args:
            id (int): The enrollment ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the report card enrollments.

        """
        if 'report_card.enrollments:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.enrollments:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/enrollments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_students_gpas(self, person_id, grading_period=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the GPA of the specified person for the report card.

        Args:
            person_id (int): The ID of the person.
            grading_period (int, optional): The grading period ID.
            school_year (int, optional): The school year.

        Returns:
            pandas.DataFrame: A DataFrame containing the GPA of the specified person for the report card.

        """
        if 'report_card.students_gpas:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.students_gpas:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/students_gpas/{person_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'grading_period': grading_period,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data['data'])

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_gpas(self, id, person_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the GPAs for a specific report card.

        Args:
            id (int): The ID of the report card.
            person_id (int): The ID of the person.

        Returns:
            pandas.DataFrame: A DataFrame containing the GPAs for the specified report card.
        """
        if 'report_card.students.gpas:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.students.gpas:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/{id}/students/{person_id}/gpas"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_numeric_grades(self, enrollment_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of numeric grades for report cards.

        Args:
            enrollment_id (int): The ID of the enrollment.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.
            x_page_number (int, optional): Page number (>= 1). Default: 1.
            x_page_size (int, optional): Number of records per page (for collection endpoints) (>= 1, <= 1000). Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of numeric grades for report cards.

        """
        if 'report_card.enrollments:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'report_card.enrollments:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/enrollments/{enrollment_id}/numeric_grades"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_numeric_grades(self, enrollment_id: int, id: int, x_api_revision: str, x_api_value_lists: str):
        """
        Get the numeric grades for a specific report card enrollment.

        Args:
            enrollment_id (int): The ID of the report card enrollment.
            id (int): The ID of the report card.
            x_api_revision (str): The revision of the API.
            x_api_value_lists (str): The value lists for the API.

        Returns:
            pandas.DataFrame: A DataFrame containing the numeric grades for the report card enrollment.
        """
        if 'report_card.enrollments.numeric_grades:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'report_card.enrollments.numeric_grades:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report-card/enrollments/{enrollment_id}/numeric-grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_card_qualitative_grades(self, enrollment_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of report card qualitative grades.

        Args:
            enrollment_id (int): The ID of the enrollment.
            x_api_revision (str, optional): The revision of the API.
            x_api_value_lists (str, optional): The value lists for the API.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The page size for pagination.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of report card qualitative grades.
        """
        if 'report_card.qualitative_grades:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.qualitative_grades:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/qualitative_grades/{enrollment_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_report_cards_qualitative_grades(self, enrollment_id, id, X_API_Revision=None, X_API_Value_Lists=None):
        """
        Read the qualitative grades for the specified report card enrollment.

        Args:
            enrollment_id (int): The ID of the report card enrollment.
            id (int): The ID of the qualitative grade.

            X_API_Revision (str, optional): The API revision.
            X_API_Value_Lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the qualitative grades for the specified report card enrollment.

        """
        if 'report_card.enrollments.qualitative_grades:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'report_card.enrollments.qualitative_grades:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"report_card/enrollments/{enrollment_id}/qualitative_grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': X_API_Revision,
            'X-API-Value-Lists': X_API_Value_Lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_staff_faculty(self, campus=None, employee_code=None, faculty_type=None, household_id=None, on_or_after_date_hired=None, on_or_after_date_terminated=None, on_or_before_date_hired=None, on_or_before_date_terminated=None, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of staff and faculty.

        Args:
            campus (int, optional): The ID of the campus.
            employee_code (int, optional): The employee code.
            faculty_type (int, optional): The ID of the faculty type.
            household_id (int, optional): The ID of the household.
            on_or_after_date_hired (str, optional): Only return staff and faculty hired on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_date_terminated (str, optional): Only return staff and faculty terminated on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_date_hired (str, optional): Only return staff and faculty hired on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_date_terminated (str, optional): Only return staff and faculty terminated on or before this specific date. Format: "YYYY-MM-DD".
            role (int, optional): The ID of the role.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of staff and faculty.

        """
        if 'staff_faculty:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'staff_faculty:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "staff-faculty"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'campus': campus,
            'employee_code': employee_code,
            'faculty_type': faculty_type,
            'household_id': household_id,
            'on_or_after_date_hired': on_or_after_date_hired,
            'on_or_after_date_terminated': on_or_after_date_terminated,
            'on_or_before_date_hired': on_or_before_date_hired,
            'on_or_before_date_terminated': on_or_before_date_terminated,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_staff_faculty(self, id=None, x_api_revision=None, x_api_value_lists=None):
        """
        Get the information of a specific staff or faculty member.

        Args:
            id (int): The ID of the staff or faculty member.

        Returns:
            pandas.DataFrame: A DataFrame containing the information of the staff or faculty member.
        """

        if 'staff_faculty:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'staff_faculty:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"staff_faculty/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_student_logistics_request(self, student_id, request_date, request_status, request_category, request_reason, request_notes, attendance_start_date, attendance_time, attendance_end_date, attendance_return_time, attendance_type, transportation_method, am_pm, bus_stop, bus_route, response_notes, internal_notes, extended_care_type, extended_care_arrival_time, extended_care_leave_time, posted, x_api_revision):
        """
        Create a logistics request for a student.

        Args:
            student_id (int): The ID of the student.
            request_date (str): The date of the request. Format: "YYYY-MM-DD".
            request_status (int): The status of the request.
            request_category (str): The category of the request.
            request_reason (str): The reason for the request.
            request_notes (str): Additional notes for the request.
            attendance_start_date (str): The start date for the attendance.
            attendance_time (str): The time of the attendance.
            attendance_end_date (str): The end date for the attendance.
            attendance_return_time (str): The return time for the attendance.
            attendance_type (int): The type of attendance.
            transportation_method (str): The method of transportation.
            am_pm (int): The AM/PM value for attendance.
            bus_stop (int): The bus stop ID.
            bus_route (str): The bus route.
            response_notes (str): Additional notes for the response.
            internal_notes (str): Internal notes regarding the request.
            extended_care_type (str): The type of extended care.
            extended_care_arrival_time (str): The arrival time for extended care.
            extended_care_leave_time (str): The leave time for extended care.
            posted (bool): Indicates if the request has been posted.

        Returns:
            pandas.DataFrame: A DataFrame containing the logistics request details.

        """
        if 'create:student-logistics-request' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'create:student-logistics-request' to your scopes.")
            return pd.DataFrame()

        endpoint = "student-logistics-requests"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'student_id': student_id,
            'date': request_date,
            'status': request_status,
            'category': request_category,
            'reason': request_reason,
            'notes': request_notes,
            'attendance_start_date': attendance_start_date,
            'attendance_time': attendance_time,
            'attendance_end_date': attendance_end_date,
            'attendance_return_time': attendance_return_time,
            'attendance_type': attendance_type,
            'transportation_method': transportation_method,
            'am_pm': am_pm,
            'bus_stop': bus_stop,
            'bus_route': bus_route,
            'response_notes': response_notes,
            'internal_notes': internal_notes,
            'extended_care_type': extended_care_type,
            'extended_care_arrival_time': extended_care_arrival_time,
            'extended_care_leave_time': extended_care_leave_time,
            'posted': posted
        }

        try:
            self.post_data_to_api(endpoint, headers, data)
            df = pd.DataFrame(data, index=[0])
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_student_logistics_requests(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_page_number=1, x_page_size=1000, x_api_revision=None, x_api_value_lists=None):
        """
        Get the list of student logistics requests.

        Args:
            on_or_after_last_modified_date (str, optional): Only return requests that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return requests that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            x_page_number (int, optional): The page number of the results to retrieve.
            x_page_size (int, optional): The number of results per page.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value lists to include.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of student logistics requests.

        """
        if 'student_logistics_requests:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'student_logistics_requests:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "student_logistics_requests"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def delete_student_logistics_request(self, id):
        """
        Delete a student logistics request.

        Args:
            id (int): The ID of the student logistics request. (Required)

        Returns:
            pandas.DataFrame: An empty DataFrame.

        """
        if 'OAuth 2.0' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"student-logistics/requests/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, None)
            print(response)

            return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_student_logistics_request(self, id):
        """
        Get the details of a student logistics request.

        Args:
            id (int): The ID of the student logistics request.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the student logistics request.

        """
        if 'student_logistics_requests:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'student_logistics_requests:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"student_logistics_requests/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string',
            'X-API-Value-Lists': 'string'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_student_logistics_request(self, id, data):
        """
        Update a student's logistics request.

        Args:
            id (int): The ID of the logistics request.
            data (dict): The updated data for the logistics request. The keys and types of the required fields are as follows:
                - student_id (int): Student ID.
                - date (str): Request Date.
                - status (int): Request Status.
                - category (str): Request Category.
                - reason (str): Request Reason.
                - notes (str): Request Notes.
                - attendance_start_date (str): Attendance Start Date.
                - attendance_time (str): Attendance Time.
                - attendance_end_date (str): Attendance End Date.
                - attendance_return_time (str): Attendance Return Time.
                - attendance_type (int): Attendance Type.
                - transportation_method (str): Transportation Method.
                - am_pm (int): AM/PM.
                - bus_stop (int): Bus Stop.
                - bus_route (str): Bus Route.
                - response_notes (str): Response Notes.
                - internal_notes (str): Internal Notes.
                - extended_care_type (str): Extended Care Type.
                - extended_care_arrival_time (str): Extended Care Arrival Time.
                - extended_care_leave_time (str): Extended Care Leave Time.
                - posted (bool): Posted.

        Returns:
            pandas.DataFrame: An empty DataFrame if the request was successful, otherwise an error message.

        """
        if 'update_student_logistics_request' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'update_student_logistics_request' to your scopes.")
            return pd.DataFrame()

        endpoint = f"update_student_logistics_request/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '1.0'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            if response.status_code == 200:
                return pd.DataFrame()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_students(self, advisor_id=None, campus_id=None, homeroom=None, homeroom_teacher_id=None, household_id=None, on_or_after_entry_date=None, on_or_after_exit_date=None, on_or_after_last_modified_date=None, on_or_before_entry_date=None, on_or_before_exit_date=None, on_or_before_last_modified_date=None, role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of students.

        Args:
            advisor_id (int, optional): Advisor ID.
            campus_id (int, optional): Campus ID.
            homeroom (int, optional): Homeroom ID.
            homeroom_teacher_id (int, optional): Homeroom Teacher ID.
            household_id (int, optional): Household ID..
            on_or_after_entry_date (str, optional): Only return students who entered on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_exit_date (str, optional): Only return students who exited on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return students who were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_entry_date (str, optional): Only return students who entered on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_exit_date (str, optional): Only return students who exited on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return students who were last modified on or before this specific date. Format: "YYYY-MM-DD".
            role (int, optional): Role ID.
            x_api_revision (str, optional): API revision.
            x_api_value_lists (str, optional): Include value lists in the response (allowed value: include).
            x_page_number (int, optional): Page number (>= 1, default: 1).
            x_page_size (int, optional): Number of records per page (>= 1, <= 1000, default: 100).

        Returns:
            pandas.DataFrame: A DataFrame containing the list of students.

        """
        if 'students:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'students:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "students"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'advisor_id': advisor_id,
            'campus_id': campus_id,
            'homeroom': homeroom,
            'homeroom_teacher_id': homeroom_teacher_id,
            'household_id': household_id,
            'on_or_after_entry_date': on_or_after_entry_date,
            'on_or_after_exit_date': on_or_after_exit_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_entry_date': on_or_before_entry_date,
            'on_or_before_exit_date': on_or_before_exit_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'role': role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_student(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the details of a student.

        Args:
            id (int): The ID of the student.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.

        Returns:
            pandas.DataFrame: A DataFrame containing the student details.

        """

        if 'read_student' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'read_student' to your scopes.")
            return pd.DataFrame()

        endpoint = f"v3/students/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_class_attendance_list(self, internal_class_id, on_or_after_attendance_date=None, on_or_after_last_modified_date=None, on_or_before_attendance_date=None, on_or_before_last_modified_date=None, person_id=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of summer class attendances.

        Args:
            internal_class_id (int): The ID of the internal class.
            on_or_after_attendance_date (str, optional): Only return attendances that occurred on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return attendances that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_attendance_date (str, optional): Only return attendances that occurred on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return attendances that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): Only return attendances for the specified person ID.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of summer class attendances.

        """
        if 'summer.classes.attendance:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.classes.attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/classes/{internal_class_id}/attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_attendance_date': on_or_after_attendance_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_attendance_date': on_or_before_attendance_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_class_attendance(self, id, internal_class_id, X_API_Revision=None, X_API_Value_Lists=None):
        """
        Read summer class attendance.

        Args:
            id (int): Class Attendance ID.
            internal_class_id (int): Internal Class ID.
            X_API_Revision (str, optional): API Revision.
            X_API_Value_Lists (str, optional): Include Value Lists in response.

        Returns:
            pandas.DataFrame: A DataFrame containing the summer class attendance data.
        """

        if 'Read Summer: Class Attendance' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Summer: Class Attendance' to your scopes.")
            return pd.DataFrame()

        endpoint = f"attendance/summer/{id}/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': X_API_Revision,
            'X-API-Value-Lists': X_API_Value_Lists
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_summer_class_attendance(self, internal_class_id, id, data: dict):
        """
        Update the attendance for a summer class.

        Args:
            internal_class_id (str): The internal ID of the summer class.
            id (str): The ID of the attendance record.
            data (dict): The data for updating the attendance record. Should include the following keys:
                - attendance_date (str): The date of the attendance in "YYYY-MM-DD" format.
                - status (int): The status of the attendance.
                - notes (str): Additional notes for the attendance.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated attendance record.

        """
        if 'summer.classes.attendance:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'summer.classes.attendance:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/classes/{internal_class_id}/attendance/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, params=data)
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_class_meeting_times(self, internal_class_id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of summer class meeting times.

        Args:
            internal_class_id (int): The internal ID of the class.

            x_api_revision (str, optional): The API revision.

            x_api_value_lists (str, optional): Include value lists in the response.

            x_page_number (int, optional): The page number.

            x_page_size (int, optional): Number of records per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of summer class meeting times.
        """
        if 'list_summer_class_meeting_times' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'list_summer_class_meeting_times' to your scopes.")
            return pd.DataFrame()

        endpoint = f"list_summer_class_meeting_times/{internal_class_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_class_meeting_times(self, id, internal_class_id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the summer class meeting times for a specific class.

        Args:
            id (int): The ID of the class.
            internal_class_id (int): The internal ID of the class.
            x_api_revision (str, optional): The API revision version.
            x_api_value_lists (str, optional): The API value lists.

        Returns:
            pandas.DataFrame: A DataFrame containing the summer class meeting times.

        """
        if 'summer.classes.meeting_times:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.classes.meeting_times:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/classes/{id}/meeting_times"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {
            'internal_class_id': internal_class_id
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_summer_classes(self, data):
        """
        Create summer classes.

        Args:
            data (dict): The data for creating summer classes.
                - class_id (str, required): Class ID.
                - description (str, required): Description.
                - status (int): Status.
                - school_year (int): School Year.
                - begin_date (str): Begin Date.
                - end_date (str): End Date.
                - primary_grade_level (int): Primary Grade Level.
                - school_level (int): School Level.
                - internal_course_id (int, required): Course ID.
                - primary_teacher_id (int): Teacher ID.
                - room_id (int): Room ID.
                - virtual_meeting_url (str): Virtual Meeting URL.

        Returns:
            pandas.DataFrame: A DataFrame containing the created summer classes.
        """
        if 'summer.classes:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.classes:create' to your scopes.")
            return pd.DataFrame()

        endpoint = f"{self.school_route}/v3/summer/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': self.headers['X-API-Revision']
        }

        try:
            response = self.fetch_data_from_api(
                'POST', endpoint, headers, data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_classes(self, last_modified_date=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, primary_teacher_id=None, room_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of summer classes.

        Args:
            last_modified_date (str, optional): Only return classes that were last modified on this specific date. Format: "YYYY-MM-DD".
            on_or_after_last_modified_date (str, optional): Only return classes that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return classes that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            primary_teacher_id (int, optional): Only return classes taught by the specified primary teacher ID.
            room_id (int, optional): Only return classes taught in the specified room ID.
            school_year (int, optional): Only return classes from the specified school year.
            x_api_revision (str, optional): API Revision.
            x_api_value_lists (str, optional): Include Value Lists in response.
            x_page_number (int, optional): Page number. Default: 1.
            x_page_size (int, optional): Number of records per page. Must be between 1 and 1000. Default: 100.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of summer classes.

        """
        if 'summer.classes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "summer/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'last_modified_date': last_modified_date,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_classes(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Read the details of a summer class.

        Args:
            id (int): The internal class ID of the summer class.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the summer class.
        """
        if 'Read Summer: Classes' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Summer: Classes' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': '1',
            'X-Page-Size': '1000'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, None)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_summer_classes(self, id, data):
        """
        Update the summer classes.

        Args:
            id (str): The ID of the summer class to be updated.
            data (dict): The data to be updated for the summer class. It should be in the format:
            {
                "class_id": str,
                "description": str,
                "status": int,
                "school_year": int,
                "begin_date": str,
                "end_date": str,
                "primary_grade_level": int,
                "school_level": int,
                "internal_course_id": int,
                "primary_teacher_id": int,
                "room_id": int,
                "virtual_meeting_url": str
            }

        Returns:
            pandas.DataFrame: A DataFrame containing the updated summer classes.

        """
        if 'summer.classes:update' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.classes:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/classes/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string'
        }

        try:
            response = requests.patch(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                data = response.json().get('data', [])
                df = pd.DataFrame(data)

                return df
            else:
                print(
                    f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_courses(self, classification=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of summer courses.

        Args:
            classification (int, optional): The classification of the summer course.
            on_or_after_last_modified_date (str, optional): Only return summer courses that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return summer courses that were last modified on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of summer courses.

        """
        if 'list_summer_courses' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'list_summer_courses' to your scopes.")
            return pd.DataFrame()

        endpoint = "summer-courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'classification': classification,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_summer_course(self, name, subject_id, course_id, catalog_title, catalog_description, x_api_revision=None):
        """
        Create a summer course.

        Args:
            name (str): The name of the summer course.
            subject_id (str): The ID of the subject.
            course_id (str): The ID of the course.
            catalog_title (str): The title of the catalog.
            catalog_description (str): Notes for the catalog.

        Returns:
            pandas.DataFrame: A DataFrame containing the created summer course.

        """
        if 'summer.courses:create' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.courses:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "summer/courses"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': str(x_api_revision),
            'Content-Type': 'application/json'
        }
        data = {
            'name': name,
            'subject_id': subject_id,
            'course_id': course_id,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description
        }

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}", headers=headers, json=data)
            if response.status_code == 200:
                created_course = response.json().get('data')
                df = pd.DataFrame([created_course])

                return df
            else:
                print(
                    f"Error: {response.status_code} - {response.text}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_courses(self, id, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the details of a specific summer course.

        Args:
            id (int): The ID of the summer course to retrieve.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): The value lists required for API.
            x_page_number (int, optional): The page number for pagination.
            x_page_size (int, optional): The number of items to return per page.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the summer course.
        """
        if 'Read Summer: Courses' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Read Summer: Courses' to your scopes.")
            return pd.DataFrame()

        endpoint = f"read-summer/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, {})
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_enrollments(self, internal_class_id=None, person_id=None, school_year=None, subject=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of summer enrollments.

        Args:
            internal_class_id (int, optional): Internal Class ID.
            person_id (int, optional): Person ID.
            school_year (int, optional): School Year.
            subject (int, optional): Subject.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of summer enrollments.

        """
        if 'list_summer_enrollments' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'list_summer_enrollments' to your scopes.")
            return pd.DataFrame()

        endpoint = "summer/enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'school_year': school_year,
            'subject': subject
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_summer_enrollments(self, id):
        """
        Get a summer enrollment by ID.

        Args:
            id (int): The ID of the summer enrollment.

        Returns:
            pandas.DataFrame: A DataFrame containing the summer enrollment data.
        """
        if 'summer.enrollments:read' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'summer.enrollments:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/enrollments/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_summer_enrollment(self, school_route, id, currently_enrolled=None, late_date_enrolled=None, date_withdrawn=None, level=None, notes=None, x_api_revision=None, auth_token=None):
        """
        Update the summer enrollment.

        Args:
            school_route (str): The specific school route.
            id (int): The ID of the summer enrollment to update.
            currently_enrolled (bool, optional): Indicates if the student is currently enrolled.
            late_date_enrolled (str, optional): The late date the student enrolled in the summer program. Format: "YYYY-MM-DD".
            date_withdrawn (str, optional): The date the student withdrew from the summer program. Format: "YYYY-MM-DD".
            level (int, optional): The level of the summer enrollment.
            notes (str, optional): Any additional notes related to the summer enrollment.
            x_api_revision (str, optional): The API revision.
            auth_token (str, optional): The authorization token.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated summer enrollment.

        """
        if 'update_summer_enrollment' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'update_summer_enrollment' to your scopes.")
            return pd.DataFrame()

        endpoint = f"schools/{school_route}/enrollments/{id}"
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'X-API-Revision': x_api_revision
        }
        data = {
            'currently_enrolled': currently_enrolled,
            'late_date_enrolled': late_date_enrolled,
            'date_withdrawn': date_withdrawn,
            'level': level,
            'notes': notes
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, data, method='PATCH')
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def create_summer_enrollments(self, internal_class_id: int, person_id: int, currently_enrolled: bool, late_date_enrolled: str, date_withdrawn: str, level: int, notes: str, x_api_revision=None):
        """
        Create summer enrollments.

        Args:
            internal_class_id (int): Required. Internal Class ID.
            person_id (int): Required. Person ID.
            currently_enrolled (bool): Required. Currently Enrolled.
            late_date_enrolled (str): Required. Late Date Enrolled.
            date_withdrawn (str): Required. Date Withdrawn.
            level (int): Required. Enrollment Level.
            notes (str): Required. Notes.

        Returns:
            pandas.DataFrame: A DataFrame containing the created summer enrollments.

        """
        if 'summer.enrollments:create' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'summer.enrollments:create' to your scopes.")
            return pd.DataFrame()

        endpoint = "summer/enrollments"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        params = {}

        body = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'currently_enrolled': currently_enrolled,
            'late_date_enrolled': late_date_enrolled,
            'date_withdrawn': date_withdrawn,
            'level': level,
            'notes': notes
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_qualitative_grade(self, id, data, x_api_revision=None):
        """
        Update a qualitative grade.

        Args:
            id (int): Grade ID.
            data (dict): Data for updating the grade.
            x_api_revision (str, optional): API Revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated qualitative grade.
        """
        if 'OAuth 2.0' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'OAuth 2.0' to your scopes.")
            return pd.DataFrame()

        endpoint = f"qualitative_grades/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }

        try:
            response = self.fetch_data_from_api(
                endpoint, headers, params=None, method='PATCH', json_data=data)
            df = pd.DataFrame(response)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_applicant(self, applicant_id):
        """
        Get the details of an admission applicant.

        Args:
            applicant_id (int): The ID of the applicant.

        Returns:
            pandas.DataFrame: A DataFrame containing the details of the admission applicant.

        """
        if 'admission.applicants:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.applicants:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/applicants/{applicant_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': 'string',
            'X-API-Value-Lists': 'string'
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params=None)
            df = pd.DataFrame(data)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_admission_relatives(self, email=None, first_name=None, last_name=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of admission relatives.

        Args:
            email (str, optional): The email address of the relative.
            first_name (str, optional): The first name of the relative.
            last_name (str, optional): The last name of the relative.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of admission relatives.
        """
        if 'Admission: Relatives' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'Admission: Relatives' to your scopes.")
            return pd.DataFrame()

        endpoint = "list_admission_relatives"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_admission_relatives(self, id, data, x_api_revision=None, content_type='application/json'):
        """
        Update the admission relatives.

        Args:
            id (int): The ID of the admission relative to update.
            data (dict): A dictionary containing the updated information for the admission relative.
            x_api_revision (str, optional): The API revision.
            content_type (str, optional): The content type of the request header.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated admission relative.

        """

        if 'admission.relatives:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'admission.relatives:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"admission/relatives/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'Content-Type': content_type
        }

        try:
            response = self.fetch_data_from_api(endpoint, headers, data)
            df = pd.DataFrame(response)
            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_athletics_rosters(self, internal_class_id=None, person_id=None, school_year=None, sport=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of athletics rosters.

        Args:
            internal_class_id (int, optional): Internal Class ID.
            person_id (int, optional): Person ID.
            school_year (int, optional): School Year.
            sport (int, optional): Sport.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of athletics rosters.

        """
        if 'athletics.rosters:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'athletics.rosters:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "athletics/rosters"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'internal_class_id': internal_class_id,
            'person_id': person_id,
            'school_year': school_year,
            'sport': sport
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_class_attendance(self, internal_class_id, attendance_date=None, block_description=None, block_id=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of class attendance.

        Args:
            internal_class_id (int): The internal ID of the class.

            attendance_date (str, optional): The date of the attendance in format "YYYY-MM-DD".
            block_description (str, optional): The description of the class block.
            block_id (int, optional): The ID of the class block.
            on_or_after_last_modified_date (str, optional): Only return attendance records that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return attendance records that were last modified on or before this specific date. Format: "YYYY-MM-DD".

        Returns:
            pandas.DataFrame: A DataFrame containing the list of class attendance.

        """
        if 'classes.attendance:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'classes.attendance:list' to your scopes.")
            return pd.DataFrame()

        endpoint = f"classes/{internal_class_id}/attendance"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'attendance_date': attendance_date,
            'block_description': block_description,
            'block_id': block_id,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_directory_preferences_person(self, id, x_api_revision=None, x_api_value_lists=None):
        """
        Get the directory preferences for a specific person.

        Args:
            id (int): The ID of the person.
            x_api_revision (str, optional): The API revision.
            x_api_value_lists (str, optional): Include value lists in the response.

        Returns:
            pandas.DataFrame: A DataFrame containing the directory preferences for the person.

        """
        if 'Read Directory Preferences: Person' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'Read Directory Preferences: Person' to your scopes.")
            return pd.DataFrame()

        endpoint = f"directory/preferences/people/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_emergency_contacts(self, legal_custody=None, medical_notification=None, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, person_id=None, pick_up=None, relationship=None, student_id=None, student_role=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=100):
        """
        Get the list of emergency contacts.

        Args:
            legal_custody (bool, optional): Legal custody indicator.
            medical_notification (bool, optional): Medical notification indicator.
            on_or_after_last_modified_date (str, optional): Only return contacts that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return contacts that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            person_id (int, optional): The ID of the person.
            pick_up (bool, optional): Pick up indicator.
            relationship (int, optional): The ID of the relationship.
            student_id (int, optional): The ID of the student.
            student_role (int, optional): The role of the student.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of emergency contacts.

        """
        if 'emergency_contacts:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'emergency_contacts:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "emergency-contacts"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'legal_custody': legal_custody,
            'medical_notification': medical_notification,
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'person_id': person_id,
            'pick_up': pick_up,
            'relationship': relationship,
            'student_id': student_id,
            'student_role': student_role
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_emergency_contact(self, id):
        """
        Get the emergency contact with the specified ID.

        Args:
            id (int): The ID of the emergency contact.

        Returns:
            pandas.DataFrame: A DataFrame containing the emergency contact information.

        """
        if 'emergency_contact:read' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'emergency_contact:read' to your scopes.")
            return pd.DataFrame()

        endpoint = f"emergency_contacts/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': '',
            'X-API-Value-Lists': ''
        }
        params = {}

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_events(self, campus=None, event_type=None, grade_level=None, internal_group_id=None, on_or_after_start_date=None, on_or_after_update_date=None, on_or_before_end_date=None, on_or_before_update_date=None, public=None, resource_id=None, school_level=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of events.

        Args:
            campus (int, optional): The ID of the campus.
            event_type (int, optional): The ID of the event type.
            grade_level (int, optional): The grade level of the event.
            internal_group_id (int, optional): The ID of the internal group.
            on_or_after_start_date (str, optional): Only return events that start on or after this specific date. Format: "YYYY-MM-DD".
            on_or_after_update_date (str, optional): Only return events that were updated on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_end_date (str, optional): Only return events that end on or before this specific date. Format: "YYYY-MM-DD".
            on_or_before_update_date (str, optional): Only return events that were updated on or before this specific date. Format: "YYYY-MM-DD".
            public (bool, optional): Indicates if the event is public or not.
            resource_id (int, optional): The ID of the resource associated with the event.
            school_level (int, optional): The ID of the school level.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of events.

        """
        if 'events.group_events:list' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'events.group_events:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "events/group_events"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'campus': campus,
            'event_type': event_type,
            'grade_level': grade_level,
            'internal_group_id': internal_group_id,
            'on_or_after_start_date': on_or_after_start_date,
            'on_or_after_update_date': on_or_after_update_date,
            'on_or_before_end_date': on_or_before_end_date,
            'on_or_before_update_date': on_or_before_update_date,
            'public': public,
            'resource_id': resource_id,
            'school_level': school_level
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def get_extended_care_classes(self, on_or_after_last_modified_date=None, on_or_before_last_modified_date=None, primary_teacher_id=None, room_id=None, school_year=None, x_api_revision=None, x_api_value_lists=None, x_page_number=1, x_page_size=1000):
        """
        Get the list of extended care classes.

        Args:
            on_or_after_last_modified_date (str, optional): Only return classes that were last modified on or after this specific date. Format: "YYYY-MM-DD".
            on_or_before_last_modified_date (str, optional): Only return classes that were last modified on or before this specific date. Format: "YYYY-MM-DD".
            primary_teacher_id (int, optional): Only return classes taught by the specified primary teacher ID.
            room_id (int, optional): Only return classes taught in the specified room ID.
            school_year (int, optional): Only return classes from the specified school year.
            x_api_revision (str, optional): The value of the X-API-Revision header.
            x_api_value_lists (str, optional): The value of the X-API-Value-Lists header.
            x_page_number (int, optional): The page number of the results to retrieve. Default is 1.
            x_page_size (int, optional): The number of results per page. Default is 1000.

        Returns:
            pandas.DataFrame: A DataFrame containing the list of extended care classes.

        """
        if 'extended-care.classes:list' not in self.scopes:
            print(
                "Error: You don't have the required scope for this endpoint. Please add 'extended-care.classes:list' to your scopes.")
            return pd.DataFrame()

        endpoint = "extended-care/classes"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision,
            'X-API-Value-Lists': x_api_value_lists,
            'X-Page-Number': str(x_page_number),
            'X-Page-Size': str(x_page_size)
        }
        params = {
            'on_or_after_last_modified_date': on_or_after_last_modified_date,
            'on_or_before_last_modified_date': on_or_before_last_modified_date,
            'primary_teacher_id': primary_teacher_id,
            'room_id': room_id,
            'school_year': school_year
        }

        try:
            data = self.fetch_data_from_api(endpoint, headers, params)
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

    def update_summer_course(self, id, name=None, course_id=None, classification=None, catalog_title=None, catalog_description=None, subject_id=None, subject_description=None, department_description=None, x_api_revision=None):
        """
        Update a summer course.

        Args:
            id (str): The ID of the course to be updated.
            name (str, optional): The name of the course.
            course_id (str, optional): The course ID.
            classification (int, optional): The classification of the course.
            catalog_title (str, optional): The catalog title of the course.
            catalog_description (str, optional): The catalog description of the course.
            subject_id (int, optional): The ID of the subject.
            subject_description (str, optional): The description of the subject.
            department_description (str, optional): The description of the department.
            x_api_revision (str, optional): The API revision.

        Returns:
            pandas.DataFrame: A DataFrame containing the updated summer course.
        """

        if 'summer.courses:update' not in self.scopes:
            print("Error: You don't have the required scope for this endpoint. Please add 'summer.courses:update' to your scopes.")
            return pd.DataFrame()

        endpoint = f"summer/courses/{id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-API-Revision': x_api_revision
        }
        body_data = {
            'name': name,
            'course_id': course_id,
            'classification': classification,
            'catalog_title': catalog_title,
            'catalog_description': catalog_description,
            'subject_id': subject_id,
            'subject_description': subject_description,
            'department_description': department_description
        }

        try:
            response = self.send_request('PATCH', endpoint, headers, body_data)
            data = response.json()
            df = pd.DataFrame(data)

            return df

        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()
