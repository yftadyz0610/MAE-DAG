# get verb tense
def get_verb_forms(conjugator, verb_word: str):
    """
    compute all forms of a verb.

    :param
    :return: tuple, (present, third-person present, past, present continuous, present perfect)
    """
    present, third_person_present, past, present_continuous, present_perfect = '', '', '', '', ''

    try:
        for form in conjugator.conjugate(verb_word):
            if len(form) == 4:
                _, tense, sub, verb = form
                if sub in ('we', 'they', 'you'):
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
            else:  # 3
                continue
        stat = 0
    except:
        # print(traceback.format_exc(()))
        stat = -1

    return (present, third_person_present, past, present_continuous, present_perfect), stat


def clean_sent(sentence: str):
    res = sentence.replace("'ve", ' have').replace("'ll", ' will').replace("'re", ' are').replace("'m", ' am').replace(
        "'d", ' would').replace("n't", ' not')

    res = res.replace("he's", 'he has').replace("she's", 'she has').replace("it's", 'it is')

    res = res.replace("He's", 'He has').replace("She's", 'She has').replace("It's", 'It is')

    res = res.replace("<br />", ' ').replace("<br/>", ' ')

    res = res.replace("(", ' ').replace(")", ' ')  # this apple (brand is blablabla)

    res = res.replace(";", '.').replace(":", '.')  # E.g.: I was excited to find these two teas because they are the perfect compromise: just enough caffeine to keep me going, but not enough to make my heart pound.

    res = res.replace('"', ' ')  # E.g.: I do not care for the "Creamy Peanut Butter".

    return res


def detect_tense(simple_sentence_pos_tag):
    # Input
    #   simple_sentence_pos_tag: POS_TAG (a list) of a SIMPLE sentence
    # Output
    #   past/modal/present_future
    #
    # it's hard to tell a future from a present.

    # detecting priority: modal (MD) > past (VBD, VBN) > present_future (others)
    # MD  Modal verb (can, could, may, must)
    # VB  Base verb (take)
    # VBC Future tense, conditional
    # VBD Past tense (took)
    # VBF Future tense
    # VBG Gerund, present participle (taking)
    # VBN Past participle (taken)
    # VBP Present tense (take)
    # VBZ Present 3rd person singular (takes)

    for tag in simple_sentence_pos_tag:
        if tag == 'MD':
            return 'modal'
    for i, tag in enumerate(simple_sentence_pos_tag):
        if tag == 'VBD':
            return 'past'
        if tag == 'VBN':
            return 'past'
    return 'present_future'