# Nurture Belief

import json
import pandas as pd

class Belief(object):

    def __init__(self,config):
        self.belief={}
        self.config=config

    @staticmethod
    def polarize_emo(emo_dict):
        res_pos, res_neg = {}, {}

        pos_d = ['Joy', 'Love']
        neg_d = ['Anger', 'Fear', 'Sadness']
        for domain, sub_domain_dict in emo_dict.items():
            if domain in pos_d:
                for sub_domain, word_list in sub_domain_dict.items():
                    for w in word_list:
                        res_pos[w] = 1
            if domain in neg_d:
                for sub_domain, word_list in sub_domain_dict.items():
                    for w in word_list:
                        res_neg[w] = 1
        return res_pos, res_neg

    def load_actions(self):
        # Mental: a mental action happens inside human beings and isn't visible. You engage in covert behaviour when you think since no one can see you thinking.
        # Physical: a physical action is a behaviour that's visible and happens outside of human beings. Examples of overt behaviour include eating or drinking something and taking part in sports, such as football or riding a bicycle.
        # Social: social behavior accounts for actions directed at others. It is concerned with the considerable influence of social interaction and culture, as well as ethics, interpersonal relationships, politics, and conflict.
        with open(self.config['action_type'], "r") as infile:
            action_type = json.load(infile)
        return action_type

    def load_belief(self):

        with open(self.config['food_entity'], "r") as infile:
            food_entity = json.load(infile)

        # only use adj from sentiwordnet
        sentinet = pd.read_csv(self.config['senti_wordnet'])
        pos_exp_adj = {}
        for st in sentinet.loc[(sentinet.POS == 'a') & (sentinet.PosScore > 0.6), 'SynsetTerms']:
            for x in st.split(' '):
                pos_exp_adj[x.split('#')[0]] = 1

        """neg_adj = {}
        for st in sentinet.loc[(sentinet.POS == 'a') & (sentinet.NegScore > 0.33), 'SynsetTerms']:
            for x in st.split(' '):
                neg_adj[x.split('#')[0]] = 1"""
        # sentiwordnet (neg_score>0.33) + LLM filtering
        with open(self.config['neg_exp_adj'], "r") as infile:
            neg_exp_adj = json.load(infile)
        with open(self.config['neg_exp_adj_badcases'], "r") as infile:
            neg_exp_adj_bad = json.load(infile)

        # emo
        with open(self.config['emo_adj'], "r") as infile:
            emo_adj = json.load(infile)
        with open(self.config['emo_verb'], "r") as infile:
            emo_verb = json.load(infile)

        with open(self.config['emo_pos_badcases'], "r") as infile:
            emo_pos_badcases = json.load(infile)
        with open(self.config['emo_neg_badcases'], "r") as infile:
            emo_neg_badcases = json.load(infile)

        # remove badcases
        emo_verb['Anger']['Irritation'].remove('eat')
        emo_verb['Anger']['Rage'].remove('eat')
        emo_adj['Anger']['Irritation'].remove('eat')
        emo_adj['Anger']['Rage'].remove('eat')

        emo_adj_pos, emo_adj_neg=Belief.polarize_emo(emo_adj)
        emo_verb_pos, emo_verb_neg=Belief.polarize_emo(emo_verb)

        self.belief['food_entity'] = food_entity
        self.belief['sentinet'] = {}
        self.belief['sentinet']['positive'] = pos_exp_adj
        self.belief['sentinet']['negative'] = neg_exp_adj
        self.belief['emotion'] = {}
        self.belief['emotion']['positive'], self.belief['emotion']['negative'] = {**emo_adj_pos, **emo_verb_pos}, {**emo_adj_neg, **emo_verb_neg}
        for w in emo_pos_badcases:
            if w in self.belief['emotion']['positive']:
                self.belief['emotion']['positive'].pop(w)
        for w in emo_neg_badcases:
            if w in self.belief['emotion']['negative']:
                self.belief['emotion']['negative'].pop(w)
        for w in neg_exp_adj_bad:
            if w in self.belief['sentinet']['negative'] :
                self.belief['sentinet']['negative'].pop(w)
        self.belief['action_type']=self.load_actions()

    def revise_belief(self):
        '''
        (1) for ethic concerns, dog is not food;

        :return:
        '''
        if 'dog' in self.belief['food_entity']:
            self.belief['food_entity'].pop('dog')
        self.belief['emotion']['positive'].pop('go')


    @staticmethod
    def check_dict(_dict, example_cnt=5):
        # _dict is a one-level dictionary
        print(list(_dict.keys())[:example_cnt])
        print(list(_dict.values())[:example_cnt])
        print("Elements Number: %d." % len(list(_dict.keys())))
        print("------------------------------")

    def check_memory(self, example_cnt=5):
        print('food_entity')
        Belief.check_dict(self.belief['food_entity'], example_cnt)

        print('sentinet::positive')
        Belief.check_dict(self.belief['sentinet']['positive'], example_cnt)
        print('sentinet::negative')
        Belief.check_dict(self.belief['sentinet']['negative'], example_cnt)

        print('emotion::negative')
        Belief.check_dict(self.belief['emotion']['positive'], example_cnt)
        print('emotion::negative')
        Belief.check_dict(self.belief['emotion']['negative'], example_cnt)

    def check_memory_v2(self, example_cnt=5, is_subdomain_thd=10):
        for k1,v1 in self.belief.items():
            if isinstance(v1,dict):
                if len(v1)<is_subdomain_thd: # find subdomains
                    for k2, v2 in v1.items():
                        print("%s::%s"%(k1,k2))
                        if isinstance(v2,dict):
                            print('dict_line1_keys_line2_values')
                            Belief.check_dict(v2, example_cnt)
                        else:
                            print('This subdomain is not a dict.')
            else:
                print("%s" % (k1))
                print('This domain is not a dict.')

    def show_domains(self):
        res=[]
        for k,v in self.belief.items():
            res.append(k)
        return res

import re
def pos_bad_check(resp):
    for s in re.split('.|,|;',resp): # sentence level
        s=s.replace('\n','').split(' ') # bag of words
        if 'False' in s:
            return True

        if 'not' in s and 'positive' in s:
            return True

    return False


if __name__=="__main__":
    from config import belief_setting

    belief=Belief(belief_setting)
    belief.load_belief()
    belief.show_domains()
    belief.check_memory_v2()
    exit(0)