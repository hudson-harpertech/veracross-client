# veracross-client

This project provides a Python wrapper for the Veracross API. It enables Veracross administrators to access, manipulate, and manage data programmatically with Python.

## Installation

Install the latest version of veracross-client by running

```
pip install --upgrade veracross-client
```

## Getting Started

To begin, you need to create an OAuth Application in Veracross using the documentation found at [Veracross Community: OAuth Applications and Veracross Overview](https://community.veracross.com/s/article/OAuth-Applications-and-Veracross-Overview). Be sure to set the scopes to cover the data you would like to access.

After creating an OAuth Application and setting its scopes, create a file named config.json similar to sample_config.json provided in this repository. It should look like:

```
{
    "client_id": "OAuth application client id",
    "client_secret": "OAuth application client secret",
    "school_route": "school route that appears in Veracross URL"
}

```

To create a client for connecting to Veracross API, use the following code:

```
import veracross_client as vc

client = vc.VeracrossClient(school_route=secrets['school_route'],
                            client_id=secrets['client_id'],
                            client_secret=secrets['client_secret'],
                            scopes=["_scope 1_","_scope 2_",...])
```

Be sure to replace the list of scopes with the scopes added to the OAuth Application. The veracross-client wrapper will return an error if a function with inappropriate scopes is used.

Once the client is initiated, use the client's methods to access individual endpoints of the Veracross API. All GET methods will return a dataframe.

## Contributing

This wrapper is still in development. Methods for individual endpoints are not guaranteed to work. Please post issues with the name of the method that is not working along with a description of the error being encountered.
