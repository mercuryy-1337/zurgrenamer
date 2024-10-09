import requests
from bs4 import BeautifulSoup
import re, os


base_url = "http://127.0.0.1:9999"
session = requests.Session()

# get the folders and items in a directory
def get_items(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    items = {}
    divs = soup.find_all('div', {'style': 'display: flex; align-items: center; gap: 5px;'})

    for div in divs:
        a_tag = div.find('a')
        if a_tag and 'href' in a_tag.attrs:
            folder_name = a_tag.text.strip()
            folder_url = a_tag['href'].replace("\\", "/")
            btn = div.find('button', {'class': 'button is-small'})
            if btn and 'hx-get' in btn.attrs:
                rename_folder_url = btn['hx-get'].replace("\\", "/")
                if folder_url not in items:
                    items[folder_url] = {
                        'folder_name': folder_name,
                        'folder_url': folder_url,
                        'rename_folder_url': rename_folder_url,
                        'files': []
                    }
                new_folder_url = base_url + folder_url
                folder_response = requests.get(new_folder_url)
                folder_soup = BeautifulSoup(folder_response.content, 'html.parser')
                file_divs = folder_soup.find_all('div', {'style': 'display: flex; align-items: center; gap: 5px;'})

                for file_div in file_divs:
                    file_btn = file_div.find('button', {'class': 'button is-small'})
                    if file_btn and 'hx-get' in file_btn.attrs:
                        file_name = file_btn.find_next_sibling(string=True).strip()
                        rename_file_url = file_btn['hx-get'].replace("\\", "/")
                        items[folder_url]['files'].append({
                            'file_name': file_name,
                            'rename_file_url': rename_file_url
                        })
    return list(items.values())


def rename_folder(rename_url, new_name):
    response = session.get(rename_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    rename_form = soup.find('form')
    if rename_form:
        form_data = {input_tag['name']: input_tag.get('value', '') for input_tag in rename_form.find_all('input')}
        form_data['torrent_name'] = new_name
        post_url = rename_form['hx-post']
        post_url = base_url + post_url.replace("\\", "/") 
        rename_response = session.post(post_url, data=form_data)
        return rename_response.status_code == 200
    else:
        print(f"Warning: No form found at {rename_url}")
        return False


def rename_file(rename_url, file_name, folder_name):
    tv_show_pattern = re.search(r'(S\d{2}E\d{2})', file_name, re.IGNORECASE)
    file_extension = os.path.splitext(file_name)[1]
    if tv_show_pattern:
        season_episode = tv_show_pattern.group(1).upper()
        new_file_name = f"{folder_name} - {season_episode}{file_extension}"
    else:
        new_file_name = file_name

    response = session.get(rename_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    rename_form = soup.find('form')
    if rename_form:
        form_data = {input_tag['name']: input_tag.get('value', '') for input_tag in rename_form.find_all('input')}
        
        form_data['file_name'] = new_file_name
        
        post_url = rename_form['hx-post']
        post_url = base_url + post_url.replace("\\", "/") 
        rename_response = session.post(post_url, data=form_data)
        
        return rename_response.status_code == 200
    else:
        print(f"Warning: No form found at {rename_url}")
        return False

# rename folders and files based on mapping
def bulk_rename(url, baseurl, rename_mapping):
    items = get_items(url)
    for item in items:
        # Rename the folder
        folder_name = item['folder_name']
        rename_folder_url = baseurl + item['rename_folder_url']
        if folder_name in rename_mapping:
            new_folder_name = rename_mapping[folder_name]
            if rename_folder(rename_folder_url, new_folder_name):
                print(f"Renamed folder '{folder_name}' to '{new_folder_name}'")
            else:
                print(f"Failed to rename folder '{folder_name}'")

        for file in item['files']:
            file_name = file['file_name']
            rename_file_url = baseurl + file['rename_file_url']
            if folder_name in rename_mapping:
                #print(f"{rename_mapping[folder_name]}/{file_name}")   
                if rename_file(rename_file_url, file_name, rename_mapping[folder_name]):
                    print(f"Renamed file '{file_name}' to match folder '{folder_name}' with season/episode")
                else:
                    print(f"Failed to rename file '{file_name}'")
                # print(f"/{rename_mapping[folder_name]}/{file_name}")


manage_url = base_url + "/manage"
directory_url = manage_url + "/__all__/"

# Mapping of current names to new names for testing
# ToDo: remove mappings dependency and integrate with DMO script
rename_mapping = {
    "3000.Miles.to.Graceland.2001.BD-Remux.1080p": "3000 Miles to Graceland (2001) {imdb-tt0233142}",
    "A Monster Calls 2016 REMUX 1080p Blu-ray AVC DTS-HD MA 5 1-LEGi0N": "A Monster Calls (2016) {imdb-tt3416532}",
    "A.Goofy.Movie.1995.1080p.BluRay.REMUX.AVC.DD2.0-FGT" : "A Goofy Movie (1995) {imdb-tt0113198}",
    "Avengers.Infinity.War.2018.PROPER.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT" : "Avengers: Infinity War (2018) {imdb-tt4154756}",
    "Shrek.2001.2160p.BluRay.REMUX.HEVC.DTS-X.7.1-FGT" : "Shrek (2001) {imdb-tt0126029}",
}
test_rename_mapping = {
    "9-1-1 S07 web 10bit hevc-d3g": "9-1-1 (2018) {imdb-tt7235466}",
}
reverse_911 ={
    "9-1-1 (2018) {imdb-tt7235466}" : "9-1-1 S07 web 10bit hevc-d3g",
}
reverse_mapping ={
    "3000 Miles to Graceland (2001) {imdb-tt0233142}" : "3000.Miles.to.Graceland.2001.BD-Remux.1080p",
    "A Monster Calls (2016) {imdb-tt3416532}" : "A Monster Calls 2016 REMUX 1080p Blu-ray AVC DTS-HD MA 5 1-LEGi0N",
    "A Goofy Movie (1995) {imdb-tt0113198}" : "A.Goofy.Movie.1995.1080p.BluRay.REMUX.AVC.DD2.0-FGT",
    "Avengers: Infinity War (2018) {imdb-tt4154756}" : "Avengers.Infinity.War.2018.PROPER.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT",
    "Shrek (2001) {imdb-tt0126029}" : "Shrek.2001.2160p.BluRay.REMUX.HEVC.DTS-X.7.1-FGT",
    "9-1-1 (2018) {imdb-tt7235466}" : "9-1-1 S07 web 10bit hevc-d3g",
}

bulk_rename(directory_url, base_url, test_rename_mapping)

