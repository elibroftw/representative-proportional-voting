# Representative Proportion Voting

As detailed in [my blog post](https://blog.elijahlopez.ca/posts/representative-proportional-voting/),
representative proportion voting is a electoral system I invented for Canada that maintains the local representation that FPTP
offers for independent runners, while assigning seats to parties in a proportional manner. This code was developed
in order to demonstrate how our house of commons would look like.

The analysis this code aided created be seen [here](https://blog.elijahlopez.ca/posts/representative-proportional-voting/#2021-general-elections-fptp-versus-rpv).

To reproduce my results, simply install the packages in `requirements.txt` via `pip install -r requirements.txt` and
run `python rpv.py` in your terminal. If you are not on Windows, you may need to use `pip3` and `python3`.

## Snippet of Blog

Vote distribution for all parties (that got at least one vote) in the 2021 Canadian Election

- There were 338 districts in this election.
- Total number of votes counted was 17,034,224
- Total votes that went to a party is 17,008,6

| Party                                     | Votes        | Vote % |
| ------------------------------------- | ------------- | -----------
| Conservative                        | 5,747,410 | 33.74%
| Liberal                                  | 5,556,629 | 32.62%
| NDP-New Democratic Party | 3,036,329 | 17.82%
| Bloc Québécois                     | 1,301,615 | 7.64%
| People's Party - PPC            | 840,993 | 4.94%
| Green Party                          | 396,988 | 2.33%
| Free Party Canada               | 47,252 | 0.28%
| Maverick Party                      | 35,178 | 0.21%
| _Independents_                         | 25,605 | 0.15%

<details><summary>Parties that got less than 10,000 votes</summary>

| Party                                     | Votes        | Vote % |
| ------------------------------------- | ------------- | -----------
| Christian Heritage Party      | 8,985 | 0.05%
| No Affiliation                        | 6,876 | 0.04%
| Parti Rhinocéros Party       | 6,085 | 0.04%
| Libertarian                         | 4,765 | 0.03%
| Communist                        | 4,700 | 0.03%
| Marxist-Leninist                  | 4,532 | 0.03%
| Pour l'Indépendance du Québec | 2,934 | 0.02%
| Animal Protection Party | 2,546 | 0.01%
| Marijuana Party | 2,031 | 0.01%
| VCP | 1,246 | 0.01%
| Centrist | 648 | 0.00%
| National Citizens Alliance | 476 | 0.00%
| Parti Patriote | 244 | 0.00%
| CFF - Canada's Fourth Front | 105 | 0.00%
| Nationalist | 52 | 0.00%
</details>

### FPTP Results

| Party                                     | Seats | Seats % |
| ------------------------------------- | -------- | ----------- |
| People's Party - PPC            | 0        |  0%      |
| Green Party                          | 2        |  0.59% |
| NDP-New Democratic Party | 25      |  7.40% |
| Bloc Québécois                    | 32       |  9.47% |
| Conservative                         | 119    | 35.21% |
| Liberal                                   | 160    | 47.34% |

### RPV Results

The Hare quota is 50,322.

| Party                                     | Seats | Seats % |
| ------------------------------------- | -------- |----------- |
| Green Party                          | 8       |  2.37% |
| People's Party - PPC            | 17     |  5.03% |
| Bloc Québécois                    | 26      |  7.69%  |
| NDP-New Democratic Party | 61     | 18.05% |
| Liberal                                   | 111   | 32.84% |
| Conservative                         | 115   | 34.02% |
