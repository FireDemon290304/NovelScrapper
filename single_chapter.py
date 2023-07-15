from bs4 import BeautifulSoup
import requests
import re
import os


def chapter_to_txt(url=None, folder_name=None) -> None:
    """
    Scrapes the content of a chapter from the given URL and saves it to a text file within the provided subdirectory.

    Args:
        url (str): The URL of the chapter.
        folder_name (str): The name of the subdirectory to save the text file.

    Returns:
        None
    """

    # Send a GET request to the webpage
    response = requests.get(url)

    # Create a BeautifulSoup object from the response text
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the div element with the class "chapter-inner chapter-content"
    div_element = soup.find("div", class_="chapter-inner chapter-content")

    # Find all paragraph elements within the div
    paragraphs = div_element.find_all("p")

    # Generate the filepath for the text file
    file_path, filename = _gen_filepath(folder_name, soup)

    # Writing the chapter content to the text file within the subdirectory
    try:
        with open(file_path + ".txt", 'w', encoding='utf-8') as file:
            for paragraph in paragraphs:
                file.write(f'{paragraph.get_text()}\n')
    except OSError:
        print(f"Failed to convert {filename} to txt.")

    return None


def _gen_filepath(folder_name, soup=None):
    """
    Generates the file path for the text file based on the subdirectory and chapter title.

    Args:
        folder_name (str): The name of the subdirectory.
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        str: The full file path for the text file.
    """
    filename = soup.find("h1").get_text()

    # Remove disallowed characters from the filename
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Limit the filename length to 255 characters
    filename = filename[:255]

    # Creating the full path for the text file
    return os.path.join(folder_name, filename), filename


if __name__ == '__main__':
    print("Security is my passion :)")
