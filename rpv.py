"""
Canadian Elections RPV Implementation
Author: Elijah Lopez < elijahllopezz@gmail.com >
License: Non-commercial need only credit author
"""
import concurrent.futures
import csv
import os
import shutil
import sys
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
import math
from itertools import cycle
import json

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://elections.ca'
IS_FROZEN = getattr(sys, 'frozen', False)  # pyinstaller generated executable
script_path = Path(os.path.dirname(sys.executable if IS_FROZEN else  __file__))


def get_raw_data_links_e44():
    ELECTION_44 = f'{BASE_URL}/content.aspx?section=res&dir=rep/off/44gedata&document=byed&lang=e'
    r = requests.get(ELECTION_44)
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    districts_links = []
    for table in tables:
        jurisdiction = table.caption.text.strip()
        files_dir = script_path / 'general_elections' / '44' / jurisdiction
        os.makedirs(files_dir, exist_ok=True)
        for row in table.find_all('tr')[1:]:
            district_number, district_name = (el.text for el in row.find_all('td', {'class': ''}))
            filename = files_dir / f'{district_number} - {district_name}.csv'
            link = row.find_all('a')[-1]['href']
            districts_links.append({'url': f'{BASE_URL}{link}', 'jurisdiction': jurisdiction, 'district_number': district_number, 'district_name': district_name, 'filename': filename})
    return districts_links


def download_file(url, dest, force=False):
    if not os.path.exists(dest) or force:
        with requests.get(url, stream=True) as r:
            with open(dest, 'wb') as f:
                shutil.copyfileobj(r.raw, f)


def process_district(district):
    """Returns information per district helpful to run the RPV algorithm

    Args:
        district (dict): {'jurisdiction': jurisdiction, 'district_number': district_number, 'district_name': district_name, 'filename': filename}

    Returns:
        dict: {**district, 'party_to_names': {}, 'party_proportions': {}, 'votes': defaultdict(int), 'independents': set(),
                           'total_votes': int, 'total_party_votes': int, 'fptp_votes_wasted': int}
    """
    district = {**district, 'party_to_names': {}, 'party_proportions': {}, 'votes': defaultdict(int), 'independents': set()}
    party_to_names = district['party_to_names']
    first_name_key, family_name_key = 'Candidate’s First Name/Prénom du candidat', 'Candidate’s Family Name/Nom de famille du candidat'
    independents = district['independents']
    votes = district['votes']
    total_party_votes = 0
    fptp_party, fptp_winner_raw = '', ''
    filename = district.pop('filename')
    with open(filename, mode='r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            merge_with = row['Merge With/Fusionné avec']
            if not merge_with:
                party_name = row['Political Affiliation Name_English/Appartenance politique_Anglais']
                vote_count = int(row['Candidate Poll Votes Count/Votes du candidat pour le bureau'])
                name = (row[first_name_key].strip('. '), row[family_name_key].strip(' .'))
                if row['Elected Candidate Indicator/Indicateur du candidat élu'] == 'Y':
                    fptp_winner_raw = name
                    fptp_party = party_name
                if party_name == 'Independent':
                    independents.add(name)
                else:
                    if party_name not in party_to_names:
                        party_to_names[party_name] = name
                    if party_to_names[party_name][0] != name[0] or party_to_names[party_name][1] != name[1]:
                        print(f'DISCREPANCY FOUND: {party_name} of {filename.stem}')
                        print(f'DEBUG: {party_to_names[party_name][0]} {party_to_names[party_name][1]} vs {name[0]} {name[1]}')
                        if SequenceMatcher(a=party_to_names[party_name][0], b=name[0]).ratio() > 0.9 and SequenceMatcher(a=party_to_names[party_name][1], b=name[1]).ratio() > 0.9:
                            name = party_to_names[party_name]
                            print('ASSUMED DISCREPANCY IS HUMAN ERROR')
                        else:
                            print('MAJOR HUMAN ERROR OR TWO DIFFERENT PEOPLE FOR THE SAME PARTY')
                            print('INSPECT DATA FILE AND FIX ERROR OR CONTACT ELECTIONS CANADA FOR TRUTH VALUE IF INDETERMINABLE')
                            sys.exit(1)
                votes[name] += vote_count
    total_votes = sum(votes.values())
    for party_name, name in party_to_names.items():
        total_party_votes += votes[name]
        district['party_proportions'][party_name] = votes[name] / total_votes
    district['total_party_votes'] = total_party_votes
    district['total_votes'] = total_votes
    fptp_winner = max(district['votes'].items(), key=lambda t: t[1])
    district['fptp_votes_wasted'] = sum(map(lambda item: item[1], filter(lambda item: item != fptp_winner, district['votes'].items())))
    assert fptp_winner[0] == fptp_winner_raw
    district['fptp_winner'] = f'{fptp_winner[0][1]}, {fptp_winner[0][0]}'
    district['fptp_party'] = fptp_party
    district['fptp_is_independent'] = fptp_winner[0] in independents
    return district


def run_rpv(districts):
    available_districts = {}
    total_party_votes = 0
    total_votes = 0
    party_votes = defaultdict(int)
    seat_allocations = {}
    total_votes_wasted = 0

    # aggregate party votes and set rpv winners when independents won
    for district in districts.values():
        total_votes += district['total_votes']
        total_party_votes += district['total_party_votes']
        total_votes_wasted += district['fptp_votes_wasted']
        if not district['fptp_is_independent']:
            available_districts[district['district_number']] = district
            for party, name in district['party_to_names'].items():
                party_votes[party] += district['votes'][name]
        else:
            district['rpv_winner'] = district['fptp_winner']
            district_to_pick['result_change'] = False
            district_to_pick['rpv_party'] = 'Independent'
            # print(f"INFO: An independent won {district['district_number']} - {district['district_name']}")
    # ceil to make it nice on eyes and because no half votes
    hare_quota = math.ceil(total_party_votes / len(available_districts))
    # allocate seats to parties remaining
    parties_summary = []
    for party, votes in party_votes.items():
        parties_summary.append((party, votes))
        if votes >= hare_quota:
            seat_allocations[party] = 1
        if votes == 0:
            print('failed')
        # else:
            # print(f'INFO: Party "{party}" with {votes:,} votes failed to meet the threshold')
    parties_summary.append(('Independent', total_votes - total_party_votes))
    parties_summary.sort(key=lambda t: t[1], reverse=True)
    for summary in parties_summary:
        print(f'| {summary[0]} | {summary[1]:,} | {summary[1] / total_votes * 100:.2f}%')
    print('---')
    print(f'INFO: Hare quota is {hare_quota:,}')
    print(f'INFO: Total votes is {total_votes:,}')
    print(f'INFO: Total votes to parties is {total_party_votes:,}')
    print(f'INFO: Total votes wasted due to FPTP is {total_votes_wasted:,} ({total_votes_wasted / total_votes * 100:.2f}%)')
    seats_allocated = len(seat_allocations)
    while seats_allocated < len(available_districts):
        party_to_allocate = max(seat_allocations, key=lambda party: priority_calc(party_votes[party], seat_allocations[party]))
        seat_allocations[party_to_allocate] += 1
        seats_allocated += 1
    # yields (party, seats_allocated) on every next
    # sort order is ascending seats. break ties based on votes so that the party with less votes can't get more seats
    distribution_order = cycle(sorted(seat_allocations.keys(), key=lambda party: (seat_allocations[party], -party_votes)))
    import time
    while available_districts:
        party = next(distribution_order)
        if seat_allocations[party] > 0:
            seat_allocations[party] -= 1
            district_to_pick = max(available_districts.values(), key=lambda district: district['party_proportions'].get(party, 0))
            name = district_to_pick['party_to_names'][party]
            district_to_pick['rpv_winner'] = f'{name[1]}, {name[0]}'
            district_to_pick['result_change'] = district_to_pick['rpv_winner'] != district_to_pick['fptp_winner']
            del available_districts[district_to_pick['district_number']]
            district_to_pick['rpv_party'] = party

def priority_calc(votes, seats_allocated):
    return votes ** 2 / seats_allocated / (seats_allocated + 1)


def compile_election_results():
    """
    Download elections results in parallel
    """
    district_dl_links = get_raw_data_links_e44()
    districts_to_process = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=20) as executor_cpu:
        future_cpu_to_district = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor_thread:
            future_thread_to_district = {executor_thread.submit(download_file, district['url'], district['filename'], force=False) : district for district in district_dl_links}
            for future in concurrent.futures.as_completed(future_thread_to_district):
                district = future_thread_to_district[future]
                del district['url']
                future_cpu_to_district.append(executor_cpu.submit(process_district, district))
        for future in concurrent.futures.as_completed(future_cpu_to_district):
            res = future.result()
            districts_to_process[res['district_number']] = res
    print('Total districts:', len(districts_to_process))
    run_rpv(districts_to_process)
    districts_output = list(districts_to_process.values())
    for district in districts_output:
        for party in district['party_to_names']:
            district['party_to_names'][party] = [district['party_to_names'][party][0], district['party_to_names'][party][1]]
        district['votes'] = [[[k[0], k[1]], v] for k, v in district['votes'].items()]
        district['independents'] = [[k[0], k[1]] for k in district['independents']]
    with open('districts.json', 'w', encoding='utf-8') as fp:
        json.dump(districts_output, fp, indent=4)
    rows = []
    fptp_summary = defaultdict(int)
    rpv_summary = defaultdict(int)
    for district in districts_to_process.values():
        del district['party_to_names']
        del district['votes']
        del district['independents']
        del district['party_proportions']
        fptp_summary[district['fptp_party']] += 1
        rpv_summary[district['rpv_party']] += 1
    print_dict_as_table(fptp_summary, len(districts_to_process))
    print()
    print_dict_as_table(rpv_summary, len(districts_to_process))

    with open('districts.csv', 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.DictWriter(f, districts_output[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(districts_to_process.values())

def print_dict_as_table(d, total_seats):
    print(f'| {"Party":<20} | Seats | Seats % |')
    print('| ------------------------------------- | -------- |----------- |')
    for party, seats in d.items():
        percentage = f'{seats/total_seats * 100:.2f}%'.rjust(6)
        print(f'| {party:<25} | {seats} | {percentage} |')


if __name__ == '__main__':
    compile_election_results()
