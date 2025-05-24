import json
import os
from copy import deepcopy
from functools import cmp_to_key

alphabet = "AĄBCĆDEĘFGHIJKLŁMNŃOÓPRSŚTUVWYZŹŻ"


def ua_cmp(a, b):
    def alphabet_index(word):
        return [alphabet.find(c.upper()) for c in word if c.upper() in alphabet]

    return (alphabet_index(a) > alphabet_index(b)) - (alphabet_index(a) < alphabet_index(b))


def main():
    with open(os.path.abspath(f"tg_bot/misc/localization/pl.json"), "r", encoding="utf-8") as file:
        in_data = json.load(file)

    ikm = in_data["markups"]["inline"]
    continent = input("Type continent name: ").strip()
    fast_access_countries_codes = input("Type fast access countries (,): ").strip().split(",")
    fast_access_countries_codes = [i.strip() for i in fast_access_countries_codes]

    all_countries_data = {}
    for num in range(1, 6):
        key = f"countries_{continent}_{num}"
        if key not in ikm:
            break

        for twice_countries in ikm[key]:
            for country_title, country_code in twice_countries.items():
                if len(country_code) != 2:
                    break

                clearing_title = country_title[country_title.find(" ") + 1:]
                emoji = country_title[:country_title.find(" ")]
                all_countries_data.update({clearing_title: {"code": country_code, "emoji": emoji}})

    all_countries_sorted = sorted(list(all_countries_data.keys()), key=cmp_to_key(ua_cmp))

    fast_countries = []
    for country in deepcopy(all_countries_sorted):
        country_data = all_countries_data[country]
        if country_data["code"] in fast_access_countries_codes:
            all_countries_sorted.remove(country)
            fast_countries.append(country)

    fast_countries_sorted = sorted(fast_countries, key=cmp_to_key(ua_cmp))
    fast_countries_sorted.extend(all_countries_sorted)

    out_data = {}
    counter = 0
    current_page = 0
    for country_name in fast_countries_sorted:
        key = f"countries_{continent}_{current_page}"
        country_data = all_countries_data[country_name]
        row = {f"{country_data['emoji']} {country_name}": country_data["code"]}

        if not out_data:
            current_page += 1
            key = f"countries_{continent}_{current_page}"
            out_data[key] = []

        elif counter >= 12:
            counter = 0
            current_page += 1
            key = f"countries_{continent}_{current_page}"
            out_data[key] = []

        current_countries_data = out_data[key]
        if not current_countries_data:
            out_data[key].append(row)

        else:
            last_el_index = len(out_data[key]) - 1
            if len(list(out_data[key][last_el_index].keys())) == 2:
                out_data[key].append(row)

            else:
                out_data[key][last_el_index].update(row)

        counter += 1

    len_out_data = len(out_data)
    for key, value in out_data.items():
        country_page = int(key.replace(f"countries_{continent}_", ""))

        if country_page == 1 and len_out_data == 1:
            additional_data = [{
                "  ": "0",
                f"1/1": "0",
                "   ": "0"
            }]

        elif country_page == 1:
            additional_data = [{
                "  ": "0",
                f"1/{len_out_data}": "0",
                "➡️": "next_page:2"
            }]

        elif country_page == len_out_data:
            additional_data = [{
                "⬅️": f"prev_page:{len_out_data - 1}",
                f"{len_out_data}/{len_out_data}": "0",
                "  ": "0"
            }]

        else:
            additional_data = [{
                "⬅️": f"prev_page:{country_page - 1}",
                f"{country_page}/{len_out_data}": "0",
                "➡️": f"next_page:{country_page + 1}"
            }]

        additional_data.extend([
            {
                "⬅️️ Do kontynentów": "to_continents",
                "📝 Potwierdź wybór": "confirm"
            },
            {
                "🔙 Wstecz": "back"
            }
        ])

        out_data[key].extend(additional_data)

    print(json.dumps(out_data, indent=4, ensure_ascii=True))


if __name__ == "__main__":
    main()
