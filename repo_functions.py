import os
import json
import requests
from lxml import etree

PIVEAU_REPO_API_KEY = os.getenv("PIVEAU_REPO_API_KEY")


def get_piveau_repo_base_url(environment: str):
    return f"https://{environment}.bydata.de/api/hub/repo/"


def read_catalog(id, env):
    url = get_piveau_repo_base_url(env) + f"catalogues/{id}"
    headers = {"Content-Type": "application/rdf+xml", "Accept": "application/rdf+xml"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        xml_tree = etree.fromstring(response.content)
        return xml_tree
    except requests.exceptions.HTTPError as e:
        raise e
    except Exception as e:
        raise e


def write_catalog(data, id, env):
    url = get_piveau_repo_base_url(env) + f"catalogues/{id}"
    headers = {
        "X-API-Key": PIVEAU_REPO_API_KEY,
        "Content-Type": "application/rdf+xml",
    }

    try:
        response = requests.put(url, headers=headers, data=data)
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        raise e
    except Exception as e:
        raise e


def set_catalog_viz_data(data, catalog_id, environment):
    try:
        tree = read_catalog(catalog_id, environment)

        visualisation_data_element = etree.Element(
            etree.QName("https://piveau.eu/ns/voc#", "visualisationData")
        )
        visualisation_data_element.text = json.dumps(data)

        catalog = tree.find("./dcat:Catalog", tree.nsmap)
        existing_element = catalog.find("./{https://piveau.eu/ns/voc#}visualisationData", tree.nsmap)
        if existing_element is not None:
            catalog.remove(existing_element)
        catalog.append(visualisation_data_element)

        catalog_body = etree.tostring(tree, encoding="utf8", pretty_print=True)

        write_catalog(catalog_body, catalog_id, environment)

        return 'Erfolgreich in den Katalog übertragen'

    except Exception as e:
        print(f"Error setting catalog viz data: {e}")
        return f"Fehler: {e}"