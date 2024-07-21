belief_setting={
             'food_entity': 'Data/food_concept_v2_single_sense.json',
             'senti_wordnet': 'Data/SentiWordNet3.csv',
             'emo_adj': 'Data/emo_adj_new.json',
             'emo_verb': 'Data/emo_verb_new.json',
             'emo_pos_badcases':'Data/emo_pos_badcases.json',
             'emo_neg_badcases':'Data/emo_neg_badcases.json',
             'neg_exp_adj': 'Data/neg_exp_adj.json',
             'neg_exp_adj_badcases': 'Data/neg_exp_adj_badcases.json',
             'action_type': 'Data/action_type.json'

}

aser_setting={
    'overlap_thd': 0.6 # threshold for measuring overlapping degree between event-restore text and raw sub-sentence text
}

# original and possessive forms
personal_pronoun = {
    'i': ['i', 'I', 'me'],
    'you': ['you', 'your'],
    'he': ['he', 'him', 'his'],
    'she': ['she', 'her'],
    'it': ['it', 'its'],
    'we': ['we', 'us', 'our'],
    'they': ['they', 'them', 'their'],
}

