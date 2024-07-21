"""
Emotion part of Nurture Belief.

The adj/verb extentions are similar words of seeds from Merriam-Webster Dictionary.
All extentions will be merged into six primary emotions: Anger, Fear, Joy, Love, Sadness, and Surprise,
and 25 secondary emotions.

Fixed problems:
    (1) base form and third-person singular form of emotion verbs are missed. (**Depreciated** This problem doesn't exist at all. Third-person singular form is not needed in this project due to ASER.)

"""
import json
import copy
import traceback

from mlconjug3 import Conjugator

def read_seed(json_file_path):
    with open(json_file_path, "r") as infile:
        seed = json.load(infile)
    return seed

def read_extended(text_file_path):
    res={} # {verb:extended_verb_list}
    with open(text_file_path) as f:
        lines = f.readlines()
    for i,verb in enumerate(lines):
        if verb[0]=='#': # find a seed verb
            seed=verb.replace('#','').replace("'",'').replace(",",'').replace("\n",'')
            ext=[]
            res[seed]=ext
            ext.append(seed)
        else: # find an extension verb
            ext.append(verb.replace('\n',''))

    return res


def merge(seed,ext):
    res=copy.deepcopy(seed)
    for c1, tmp in seed.items():
        for c2, w_list in tmp.items():
            for w in w_list:
                if w in ext:
                    res[c1][c2]+=ext[w]
    # remove duplicated words
    for c1, tmp in res.items():
        for c2, _ in tmp.items():
            res[c1][c2]=list(set(res[c1][c2]))
    return res


def get_past_tense(all_conjugated_forms):
    for _, tense, sub, verb in all_conjugated_forms:
        if "past tense" in tense:
            return verb
    return "unknown"

def get_present_continuous(all_conjugated_forms):
    for _, tense, sub, verb in all_conjugated_forms:
        if "present continuous" in tense:
            return verb
    return "unknown"

def trans_verb2adj(conjugator, verbs:list):
    """
    Transform verb to its past and present tenses which are usually used as adjectives.
    We admit that some past and present tenses could not be used as adj, therefore this pseudo "adj" set
    should be used together with POS. If a word has adj POS and also hit our pseudo "adj" set, we could safely add the
    emotion tag in pseudo "adj" set to this word.

    :param emo_verb: two level
    :return:
    """
    res=set()
    succ=0
    for v in verbs:
        try:
            tmp=conjugator.conjugate(v)
            res.add(get_past_tense(tmp))
            res.add(get_present_continuous(tmp))
            succ += 1
        except:
            continue
    res=list(res)
    if 'unknown' in res:
        res.remove('unknown')
    return res, succ/(len(verbs)+1)


def get_verb_forms(conjugator, verb_word: str):
    """
    compute all forms of a verb.

    :param
    :return: tuple, (present, third-person present, past, present continuous, present perfect)
    """
    present, third_person_present, past, present_continuous, present_perfect = '', '', '', '', ''

    try:
        for form in conjugator.conjugate(verb_word):
            if len(form)==4:
                _, tense, sub, verb = form
                if sub in ('we','they','you'):
                    continue
                if tense == 'indicative present' and sub == 'I':
                    present = verb
                if tense == 'indicative present' and sub == 'he/she/it':
                    third_person_present = verb
                if tense == 'indicative past tense' and sub == 'I':
                    past = verb
                if tense == 'indicative present continuous' and sub == 'I':
                    present_continuous = verb
                if tense == 'indicative present perfect' and sub == 'I':
                    present_perfect = verb
            else: # 3
                continue
        stat = 0
    except:
        #print(traceback.format_exc(()))
        stat = -1

    return (present, third_person_present, past, present_continuous, present_perfect), stat

def merge_adj_and_verb_emo_dict(conjugator, emo_adj:dict,emo_verb:dict):
    """
    :param emo_adj: two-level dict
    :param emo_verb: two-level dict
    :return: two-level dict
    """
    total=0
    fail=0
    res=copy.deepcopy(emo_adj)
    for c1, tmp in emo_adj.items():
        for c2, w_list in tmp.items():
            w_list_added=[]
            for v in emo_verb[c1][c2]:
                total+=1
                forms,stat=get_verb_forms(conjugator, v)
                if stat==-1:
                    forms=(v,'','','','') # only add the original words
                    fail+=1
                for w in forms:
                    if w not in w_list:
                        w_list_added.append(w)
            res[c1][c2]+=w_list_added
            print("%s >> %s \n \t Added verb number: %d"%(c1,c2,len(w_list_added)))

    # remove duplicated words
    for c1, tmp in res.items():
        for c2, _ in tmp.items():
            res[c1][c2]=list(set(res[c1][c2]))

    print('Failing rate: %.2f'%(fail/total))

    return res

def extend_adj_with_verb(conjugator, emo_adj:dict,emo_verb:dict):
    """
    :param emo_adj: two-level dict
    :param emo_verb: two-level dict
    :return: two-level dict
    """
    res=copy.deepcopy(emo_adj)
    for c1, tmp in emo_adj.items():
        for c2, w_list in tmp.items():
            verb2adj_list, succ_ratio=trans_verb2adj(conjugator, emo_verb[c1][c2])
            res[c1][c2]+=verb2adj_list
            print("%s >> %s \n \t Success Rate: %.2f"%(c1,c2,succ_ratio))
    # remove duplicated words
    for c1, tmp in res.items():
        for c2, _ in tmp.items():
            res[c1][c2]=list(set(res[c1][c2]))
    return res

def remove_black(emo:dict,black_words: list):
    res=emo
    cnt=0
    for c1, tmp in emo.items():
        for c2, w_list in tmp.items():
            for w in w_list:
                if w in black_words:
                    res[c1][c2].remove(w)
                    cnt+=1
    print("Removed WordNum: %d" % (cnt))
    return res

def read_words(file_path:str):
    res=[]
    with open(file_path) as f:
        lines = f.readlines()
    res=[w.replace('\n','') for w in lines]
    return res

def count_w(emo:dict,display_sub=True, return_total=False):
    total=[]
    for c1, tmp in emo.items():
        for c2, w_list in tmp.items():
            total+=w_list
            if display_sub:
                print("%s >> %s \n \t WordNum: %d" % (c1, c2, len(w_list)))
    print("Total WordNum: %d" % (len(total)))
    if return_total:
        return total



if __name__=="__main__":
    verb_seed = 'Data/emo_verb_seed.json'
    adj_seed = 'Data/emo_adj_seed.json'
    verb_ext='Data/emo_verb_extention.txt'
    adj_ext = 'Data/emo_adj_extention.txt'
    # black_words='Data/black_words.txt'

    verb_seed=read_seed(verb_seed)
    verb_ext=read_extended(verb_ext)
    emo_verb=merge(verb_seed,verb_ext)
    emo_verb_new=copy.deepcopy(emo_verb)
    for w in emo_verb['Joy']['Optimism']:
        emo_verb_new['Joy']['Optimism'].remove(w)

    #blacks=read_words(black_words)
    #emo_verb_new=remove_black(emo_verb,blacks)
    # emo_verb['Joy']['Optimism']

    #with open('Data/emo_verb.json', 'w') as outfile:
    #    json.dump(emo_verb, outfile)
    #with open("Data/emo_verb_new.json", "w") as outfile:
    #    json.dump(emo_verb_new, outfile)
    #print('---- verb seed ----')
    #count_w(verb_seed)
    print('---- verb merged ----')
    count_w(emo_verb_new)


    adj_seed = read_seed(adj_seed)
    adj_ext = read_extended(adj_ext)
    emo_adj = merge(adj_seed, adj_ext)
    #print('---- adj seed ----')
    #count_w(adj_seed)
    print('---- adj merged ----')
    count_w(emo_adj)


    conjugator = Conjugator(language='en')
    emo_adj_verb_all=merge_adj_and_verb_emo_dict(conjugator, emo_adj, emo_verb_new)
    print('---- ALL FINAL ----')
    count_w(emo_adj_verb_all)

    with open("Data/emo_adj_verb_all.json", "w") as outfile: # two-levels emo tags: adj(seed+ext) + all forms of verb (seed +ext)
        json.dump(emo_adj_verb_all, outfile)
    exit(0)



