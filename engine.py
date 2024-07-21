# Core elements of extracting MAE-DAG given ASER events.

import joblib
from queue import Queue
import pickle
import tqdm
from utils import detect_tense

class Counter(object):
    def __init__(self):
        self.node_id = -1
    def generate_node_id(self):
        self.node_id+=1
        return self.node_id

class Node(object):
    def __init__(self,name,id,activate_thd=1,output_signal=1):
        self.name=name
        self.id=id
        self.activate_thd=activate_thd
        self.output_signal=output_signal
        self.is_active=False
        self.active_value=0
        self.children=[]

    def add_children(self,children_nodes:list):
        for child in children_nodes:
            if child in self.children:
                print('Child %s has existed.'%child.__repr__)
            else:
                self.children.append(child)

    # for design
    def link(self,children_nodes:list):
        for child in children_nodes:
            if child in self.children:
                pass
            else:
                self.children.append(child)

    # for transmit
    def pulse(self):
        return self.output_signal

    def del_children(self,children_nodes:list):
        for child in children_nodes:
            if child not in self.children:
                print('Child %s does not existed.'%child.__repr__)
            else:
                self.children.remove(child)

    def reset_children(self):
        self.children=[]

    def set_active(self):
        self.is_active = True

    def set_inactive(self):
        self.is_active = False

    @property
    def _children(self):
        return self.children

    @property
    def _id(self):
        return self.id

    @property
    def _activeStatus(self):
        return self.is_active

    @property
    def _activeThd(self):
        return self.activate_thd

    @property
    def _activeValue(self):
        return self.active_value

    def __repr__(self):
        return self.name

class Mapper(object):
    # indexer
    def __init__(self):
        self.node_id_map={}
        self.node_name_map={}

    def add_nodes(self,nodes:list):
        for node in nodes:
            if node.id not in self.node_id_map:
                self.node_id_map[node.id]=node
                self.node_name_map[node.name]=node

    def has_node(self,name):
        if name in self.node_name_map:
            return True
        else:
            return False

    def find_node_by_name(self, name):
        if name not in self.node_name_map:
            return -1, None
        else:
            return 0, self.node_name_map[name]

    def find_nodes_by_name(self, names:list):
        res=[]
        for name in names:
            if name not in self.node_name_map:
                raise Exception("%s does not exist in node mapper."%name)
            else:
                res.append(self.node_name_map[name])
        return res

    def show_node_names(self):
        return [ x for x in self.node_name_map.keys()]

    @property
    def _node_name_map(self):
        return self.node_name_map

# computing framework
class Engine(object):
    def __init__(self,memory):
        pass

    @staticmethod
    def extract_np(aser_event):
        # extract noun phrase
        res = []
        vb=set()
        vb_full=dict() # {vb_word: list}
        for d in aser_event.dependencies:
            h = d[0]
            hw = h[1]
            h_pos = h[2]

            r = d[1]

            t = d[2]
            tw = t[1]
            t_pos = t[2]

            # for adj, only keep JJ+NN or NN+BE+JJ
            # JJ+NN (a delicious apple): JJ in tail; NN+BE+JJ (this apple is delicious): JJ in head
            if ('JJ' in h_pos and 'NN' in t_pos) :
                res.append((hw, tw))
            if ('JJ' in t_pos and 'NN' in h_pos):
                res.append((tw, hw))

            # VB
            if ('VB' in t_pos):
                vb.add(tw)
            if ('VB' in h_pos):
                vb.add(hw)
                if hw not in vb_full:
                    vb_full[hw]=[]
                vb_full[hw].append(d)

        return res

    @staticmethod
    def extract_core(aser_event,restore_text):
        # extract core information of the given aser_event
        core={}
        jjnn = []
        prjj = []
        nn=set()
        vb=set()
        head_vb_info=dict() # only keep 'head' verbs info
        tail_vb_info = dict()  # only keep 'tail' verbs info

        verb_info={} # {verb_word: {"sub":word, "ob": word, "xcomp": word}}

        for d in aser_event.dependencies:
            h = d[0]
            hw = h[1] # word
            h_pos = h[2] # POS

            r = d[1]

            t = d[2]
            tw = t[1] # word
            t_pos = t[2] # POS


            # JJ+NN (a delicious apple): JJ in tail; NN+BE+JJ (this apple is delicious): JJ in head
            if ('JJ' in h_pos and 'NN' in t_pos) :
                jjnn.append((hw, tw))
            if ('JJ' in t_pos and 'NN' in h_pos):
                jjnn.append((tw, hw))

            # PR + BE + JJ
            if ('JJ' in h_pos and 'PR' in t_pos) :
                prjj.append((tw, hw))

            # NN
            if ('NN' in t_pos):
                nn.add(tw)
            if ('NN' in h_pos):
                nn.add(hw)

            # VB
            if ('VB' in t_pos):
                vb.add(tw)
                if tw not in tail_vb_info:
                    tail_vb_info[tw]=[]
                tail_vb_info[tw].append(d)
            if ('VB' in h_pos):
                vb.add(hw)
                if hw not in head_vb_info:
                    head_vb_info[hw]=[]
                head_vb_info[hw].append(d)

        # PR + V + JJ
        for v,dep_list in head_vb_info.items():
            _pr=''
            _jj=''
            for d in dep_list:
                r = d[1]
                t = d[2]
                tw = t[1]  # word
                t_pos = t[2]  # POS
                if r=='nsubj' and 'PR' in t_pos:
                    _pr=tw
                if r == 'xcomp' and 'JJ' in t_pos:
                    _jj=tw
            if _pr!='' and _jj!='':
                prjj.append((_pr, _jj))

        core['JJ+NN']=jjnn
        core['PR+JJ'] = prjj
        core['NN']=list(nn)
        core['VB']=list(vb)
        core['head_VB_info']=head_vb_info
        core['tail_VB_info']=tail_vb_info
        core['dependancy']=aser_event.dependencies
        core['tense']=detect_tense(aser_event.pos_tags)

        if 'not' in aser_event.__repr__().split(' '):
            core['has_a_not'] = True
        else:
            core['has_a_not'] = False

        return core

    @staticmethod
    def make_design(mapper, counter):
        # activating condition: activated food node & (activated emo or feeling node)
        need_food_pos = Node('#need_food_pos', counter.generate_node_id(), activate_thd=2)
        need_food_neg = Node('#need_food_neg', counter.generate_node_id(), activate_thd=2)

        food=Node('#food',counter.generate_node_id())
        food.link([need_food_pos, need_food_neg])

        # positive/neg experience feeling
        # activating condition: instance & activated_parent
        exp_pos = Node('#experience_feeling_pos', counter.generate_node_id(), activate_thd=2)
        exp_neg = Node('#experience_feeling_neg', counter.generate_node_id(), activate_thd=2)
        exp_pos.link([need_food_pos])
        exp_neg.link([need_food_neg])

        # activating condition: instance & activated_parent
        emo_pos = Node('#emo_pos', counter.generate_node_id(), activate_thd=2)
        emo_neg = Node('#emo_neg', counter.generate_node_id(), activate_thd=2)
        emo_pos.link([need_food_pos])
        emo_neg.link([need_food_neg])

        action_pos = Node('#action_pos', counter.generate_node_id())
        action_neg = Node('#action_neg', counter.generate_node_id())
        need_food_pos.link([action_pos])
        need_food_neg.link([action_neg])

        _not = Node('#not', counter.generate_node_id())

        # add #past_experience, #mental_action, #physical_action, #social_action into design.
        past_exp=Node('#past_experience', counter.generate_node_id())
        past_exp.link([exp_pos,exp_neg,emo_pos,emo_neg])

        # activating condition: instance & activated_parent
        mental_action = Node('#mental_action', counter.generate_node_id(), activate_thd=2)
        physical_action = Node('#physical_action', counter.generate_node_id(), activate_thd=2)
        social_action = Node('#social_action', counter.generate_node_id(), activate_thd=2)

        action_pos.link([mental_action, physical_action, social_action])
        action_neg.link([mental_action, physical_action, social_action])

        mapper.add_nodes(
            [food, exp_pos, exp_neg, need_food_pos, need_food_neg, emo_pos, action_pos, emo_neg, action_neg, _not,
             past_exp,mental_action,physical_action,social_action])

        # #food Food entity, e.g. bread, apple.
        # #past_experience Actions that took place in the past. e.g. bought, searched
        # #experience_feeling_pos Positive feelings, e.g. delicious, easy.
        # #experience_feeling_neg Negative feelings, e.g. bitter, hard.
        # #emo_pos Positive emotions, e.g. happy, cheerful.
        # #emo_neg Negative emotions, e.g. sad, angry.
        # #need_food_pos Human's need of food is satisfied. e.g. --
        # #need_food_neg Human's need of food is dissatisfied. e.g. --
        # #action_pos Actions that are driven to strengthen being able to continuously meet the need.
        # #action_neg Actions that are driven to prevent it from happening again when human's need is dissatisfied.
        # #mental_action Actions that happen inside human beings, not visible. e.g. analyse, versify
        # #physical_action Actions that happen outside human beings and are visible. e.g. wash, peel
        # #social_action Actions that are directed at others. e.g. denounce, rent


    @staticmethod
    def incorporate(word, node_names, mapper, active_nodes, counter, direction='child', do_activation=True):
        """
        (1) set up a node to represent `word`
        (2) activate this node and record it in `active_nodes`
        (3) index this node in mapper
        (4) link this node to its 'child'/'parent'

        Input:
            word    string,e.g."happy".
            node_names  [str of node name], e.g.["#emo_pos","#emo_neg"].
            mapper  instance of class Mapper.
            active_nodes    {instance of class Node: node._activeThd(threshold)}.
            counter instance of class Counter.
            direction 'child'/'parent'.
            do_activation   whether activate the set-up node that represents `word`.

        :return: True, if success; False if fail.
        """
        if len(node_names)==0:
            return False

        if mapper.has_node(word):
            node=mapper.find_nodes_by_name([word])[0]
        else:
            node=Node(word, counter.generate_node_id())
            mapper.add_nodes([node])

        if do_activation:
            if node in active_nodes:
                pass
            else:
                active_nodes[node] = node._activeThd
                node.set_active()

        for x in node_names:
            assert mapper.has_node(x), "Child/Parent node doesn't exist!"

        if direction=='child':
            node.link(mapper.find_nodes_by_name(node_names))

        if direction=='parent':
            for p_node in mapper.find_nodes_by_name(node_names):
                p_node.link([node])

        return True

    @staticmethod
    def perceive(event, event_info_cores, mapper, belief, active_nodes, counter, record_event=False, restore_text=None, sub_sent_text=None, overlap_thd=-1):
        # (1) Food entity + expaerience description;
        # (2) Food entity + emotion description;
        # (3) I/we + emotion description
        # (4) I/we + experience description
        # (5) Emotional action.

        '''

        :param event:
        :param event_info_cores:
        :param mapper:
        :param belief:
        :param active_nodes:
        :param counter:
        :param record_event:
        :param restore_text:
        :param sub_sent_text:
        :param overlap_thd:
        :return:
        '''

        # np = Engine.extract_np(event)  # noun phrases

        words_p = []  # perceived words
        not_node_children = []

        for _jj, _nn in event_info_cores['JJ+NN']:

            if _nn in belief.belief['food_entity']:  # a food entity is perceived

                jj_children = []
                if event_info_cores['has_a_not']:
                    # link emo
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_neg')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_pos')

                    # link sentinet
                    if _jj in belief.belief['sentinet']['positive']:
                        jj_children.append('#experience_feeling_neg')


                    if _jj in belief.belief['sentinet']['negative']:
                        jj_children.append('#experience_feeling_pos')

                else:
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_pos')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_neg')

                    # link sentinet
                    if _jj in belief.belief['sentinet']['positive']:
                        jj_children.append('#experience_feeling_pos')

                    if _jj in belief.belief['sentinet']['negative']:
                        jj_children.append('#experience_feeling_neg')

                if Engine.incorporate(_jj, jj_children, mapper, active_nodes, counter): # jj_children is not empty
                    words_p.append(_jj)
                    if event_info_cores['has_a_not']:
                        # point `not` node to _jj
                        not_node_children.append(_jj)
                    if Engine.incorporate(_nn, ['#food'], mapper, active_nodes, counter): # only when an adj is added, we add this noun, as this noun would have a more clear meaning.
                        words_p.append(_nn)

            if _nn in ('I', 'i', 'We', 'we'):  # human is perceived

                jj_children = []
                if event_info_cores['has_a_not']:
                    # link emo
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_neg')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_pos')

                else:
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_pos')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_neg')

                if Engine.incorporate(_jj, jj_children, mapper, active_nodes, counter): # jj_children is not empty
                    words_p.append(_jj)
                    if event_info_cores['has_a_not']:
                        # point `not` node to _jj
                        not_node_children.append(_jj)

        for _pr, _jj in event_info_cores['PR+JJ']:
            if _pr in ('I', 'i', 'We', 'we'):

                jj_children = []
                if event_info_cores['has_a_not']:
                    # link emo
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_neg')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_pos')

                    # link sentinet
                    if _jj in belief.belief['sentinet']['positive']:
                        jj_children.append('#experience_feeling_neg')


                    if _jj in belief.belief['sentinet']['negative']:
                        jj_children.append('#experience_feeling_neg')

                else:
                    if _jj in belief.belief['emotion']['positive']:
                        jj_children.append('#emo_pos')

                    if _jj in belief.belief['emotion']['negative']:
                        jj_children.append('#emo_neg')

                    # link sentinet
                    if _jj in belief.belief['sentinet']['positive']:
                        jj_children.append('#experience_feeling_pos')

                    if _jj in belief.belief['sentinet']['negative']:
                        jj_children.append('#experience_feeling_neg')

                if Engine.incorporate(_jj, jj_children, mapper, active_nodes, counter): # jj_children is not empty
                    words_p.append(_jj)
                    if event_info_cores['has_a_not']:
                        # point `not` node to _jj
                        not_node_children.append(_jj)


        for _vb in event_info_cores['VB']:
            vb_children = []
            if event_info_cores['has_a_not']:
                # emotional action
                if _vb in belief.belief['emotion']['positive']:  # an emotion verb is perceived
                    vb_children.append('#emo_neg')
                elif _vb in belief.belief['emotion']['negative']:  # an emotion verb is perceived
                    vb_children.append('#emo_pos')

                elif event_info_cores['tense']=='past': # past action
                    vb_children.append('#past_experience')
                else:
                    pass
            else:
                # emotional action
                if _vb in belief.belief['emotion']['positive']:  # an emotion verb is perceived
                    vb_children.append('#emo_pos')
                elif _vb in belief.belief['emotion']['negative']:  # an emotion verb is perceived
                    vb_children.append('#emo_neg')

                elif event_info_cores['tense'] == 'past':  # past action
                    vb_children.append('#past_experience')
                else:
                    pass

            if Engine.incorporate(_vb, vb_children, mapper, active_nodes, counter):
                words_p.append(_vb)
                if event_info_cores['has_a_not']:
                    # point `not` node to _vb
                    not_node_children.append(_vb)

        if len(not_node_children) > 0:
            assert Engine.incorporate('#not', not_node_children, mapper, active_nodes, counter)

        if record_event:
            # if the restore text has strong overlapping with the original sub-sentence text, we use the original text
            # e.g. event text: 'the chocolate be the best', restore text: 'the chocolate are the best', sub-sentence text: 'however the chocolate are the best', the sub-sentence text
            # would be chosen to replace the event text.

            if Engine.is_overlapped(sub_sent_text, restore_text, overlap_thd):
                Engine.incorporate(sub_sent_text, words_p, mapper, active_nodes, counter, do_activation=False)
            else:
                Engine.incorporate(restore_text, words_p, mapper, active_nodes, counter, do_activation=False)

    @staticmethod
    def transmit(active_nodes):
        # BFS
        pool = Queue(maxsize=1000000)
        for node, _ in active_nodes.items():
            pool.put(node)
        while not pool.empty():
            cur_node = pool.get()
            signal = cur_node.pulse()
            for child in cur_node._children:
                child.active_value += signal
                if (not child.is_active) and (child.active_value >= child.activate_thd):  # first time activated
                    child.set_active()
                    pool.put(child)
                    active_nodes[child] = child._activeValue
                else:  # omit already activated nodes or a node that is not met activating threshold
                    pass


    @staticmethod
    def pulse(target_node_name, pulse_value, mapper, active_nodes):
        """
        # Pulse a node by a specific value. Activate this node if its threshold is arrived.

        :return:
        """
        node = mapper.find_nodes_by_name([target_node_name])[0]
        node.active_value += pulse_value
        if node.active_value >= node._activeThd:
            active_nodes[node] = node._activeThd
            node.set_active()


    @staticmethod
    def is_valid_verb(verb, head_verb_dep_info:list):
        # s(I/We)+v+o
        if verb in ('guess'): # uncertain action, meaningless.
            return False

        sub_valid=False
        obj_valid=False
        # verb_dep_info: [((1, 'make', 'VBZ'), 'nsubj', (0, 'this', 'DT'))]
        for d in head_verb_dep_info:
            if d[1]=='nsubj' and d[2][1] in ('I','We','i','we'): # only I/we as subject
                sub_valid=True
            if len(head_verb_dep_info)==1 and d[1]=='nsubj': # s-v, e.g. "The dog barks"
                obj_valid = True
            if d[1] in ('dobj', 'xcomp', 'ccomp'): # exclude 'acomp', 'pcomp'
                obj_valid=True
            if 'nmod' in d[1]: # 'nmod:into', 'nmod:over'. s-v-p-o, e.g. "He walks into the room"
                obj_valid = True
        if sub_valid and obj_valid:
            return True
        else:
            return False


    @staticmethod
    def act(event, event_info_cores, mapper, belief, active_nodes, counter, record_event=False, restore_source=None, overlap_thd=-1):
        if mapper.has_node(event.__repr__()): # this event has already been processed in preceding phases.
            return

        words_i = []  # incorporated words

        for _vb in event_info_cores['VB']:
            if (_vb not in event_info_cores['head_VB_info']) or (not Engine.is_valid_verb(_vb, event_info_cores['head_VB_info'][_vb])):
                continue # only keep head vb with format of s(i/we)+v+o in reasoning graph
            if mapper.has_node(_vb): # already processed
                continue
            vb_parents = []
            if mapper.find_nodes_by_name(['#action_pos'])[0] in active_nodes or mapper.find_nodes_by_name(['#action_neg'])[0] in active_nodes:
                # only when #action_pos/neg is activated, then we try to capture action instances.

                if _vb in belief.belief['action_type']['mental']:
                    vb_parents.append('#mental_action')
                    # The activated action-instance node would back activate its parent node. E.g. in "I share this food.", "share" would
                    # bact activate its parent node '#social_action'.
                    Engine.pulse('#mental_action', 1, mapper, active_nodes)
                if _vb in belief.belief['action_type']['physical']:
                    vb_parents.append('#physical_action')
                    Engine.pulse('#physical_action', 1, mapper, active_nodes)
                if _vb in belief.belief['action_type']['social']:
                    vb_parents.append('#social_action')
                    Engine.pulse('#social_action', 1, mapper, active_nodes)

            if Engine.incorporate(_vb, vb_parents, mapper, active_nodes, counter, direction='parent'):
                words_i.append(_vb)

        if record_event:
            # if the restore text has strong overlapping with the original sub-sentence text, we use the original text
            # e.g. event text: 'the chocolate be the best', restore text: 'the chocolate are the best', sub-sentence text: 'however the chocolate are the best', the sub-sentence text
            # would be chosen to replace the event text.
            restore_text, subsent_text = restore_source[event.__repr__()]
            if Engine.is_overlapped(subsent_text, restore_text, overlap_thd):
                Engine.incorporate(subsent_text, words_i, mapper, active_nodes, counter, do_activation=False)
            else:
                Engine.incorporate(restore_text, words_i, mapper, active_nodes, counter, do_activation=False)

    @staticmethod
    def is_overlapped(base_text, text, thd):
        # Judge if the overlap between two pieces of text is larger than `thd`.
        # Return True or False

        base_cut=base_text.split(' ')
        text_cut=text.split(' ')

        cnt=0
        total=0
        for t in text_cut: # filter out ''
            if t!='':
                total+=1
                if t in base_cut:
                    cnt+=1
        if cnt/total>thd:
            return True
        else:
            return False

    @staticmethod
    def is_valid_event(event,restore_source):
        # (1) word number>2, (2) has restore text
        event_text=event.__repr__()

        if len(event_text.split(' '))>2 and event_text in restore_source:
            return True
        else:
            return False

    @staticmethod
    def aser_process(aser, belief, aser_restore, aser_setting):
        # aser: {text_id,events:list}
        experience = {} # {text_id, mapper}
        res = {} # {text_id, res_dict}

        for text_id,events in tqdm.tqdm(aser.items()):
            counter=Counter()
            mapper=Mapper()
            active_nodes = {}
            event_info_cores={}

            # load aser-event restore text
            if text_id not in aser_restore:
                continue
            restore=aser_restore[text_id] # {event_text:[restore_event_text, sub_sent_text]}

            Engine.make_design(mapper, counter)
            for event_list in events:
                for e in event_list:
                    # valid event
                    if Engine.is_valid_event(e,restore): # (1) word number>2, (2) has restore text
                        restore_text, sub_sent_text =restore[e.__repr__()]
                        event_info_cores[e] = Engine.extract_core(e,restore_text)
                        Engine.perceive(e,event_info_cores[e], mapper,belief,active_nodes,counter,record_event=True,
                                        restore_text=restore_text, sub_sent_text=sub_sent_text, overlap_thd=aser_setting['overlap_thd'])
            Engine.transmit(active_nodes)
            for event_list in events:
                for e in event_list:
                    if Engine.is_valid_event(e, restore):
                        Engine.act(e, event_info_cores[e], mapper, belief, active_nodes, counter, record_event=True,
                                   restore_source=restore, overlap_thd=aser_setting['overlap_thd'])

            # save
            res[text_id] = {}
            res[text_id]['mapper'] = mapper
            res[text_id]['counter'] = counter
            res[text_id]['event_info_cores'] = event_info_cores
            res[text_id]['active_nodes'] = active_nodes

        return res

    @staticmethod
    def debug_aser_process(events,belief, restore, aser_setting):
        # text_id level

        counter=Counter()
        mapper=Mapper()
        active_nodes = {}
        event_info_cores={}

        Engine.make_design(mapper, counter)
        for event_list in events:
            for e in event_list:
                # valid event
                if Engine.is_valid_event(e, restore):
                    restore_text, sub_sent_text = restore[e.__repr__()]
                    event_info_cores[e] = Engine.extract_core(e, restore_text)
                    Engine.perceive(e, event_info_cores[e], mapper, belief, active_nodes, counter, record_event=True,
                                    restore_text=restore_text, sub_sent_text=sub_sent_text,
                                    overlap_thd=aser_setting['overlap_thd'])
        Engine.transmit(active_nodes)
        for event_list in events:
            for e in event_list:
                if Engine.is_valid_event(e, restore):
                    Engine.act(e, event_info_cores[e], mapper, belief, active_nodes, counter, record_event=True,
                               restore_source=restore, overlap_thd=aser_setting['overlap_thd'])

        res= {}
        res['mapper'] = mapper
        res['counter'] = counter
        res['event_info_cores'] = event_info_cores
        res['active_nodes'] = active_nodes

        return res


    @staticmethod
    def debug_np(event):
        np = Engine.extract_np(event)
        dep=event.dependencies
        return

    @staticmethod
    def debug_custom(text):
        pass

if __name__=="__main__":
    from belief import Belief
    from config import belief_setting, aser_setting, personal_pronoun
    from restore_event import restore_event
    from mlconjug3 import Conjugator

    conjugator = Conjugator(language='en')

    belief = Belief(belief_setting)
    belief.load_belief()
    belief.revise_belief()


    # ------------ single debug ------------- #
    # text_id=452556
    # # aser = joblib.load('Data/amazon_food_review_aser_event_for_valid_all.%s'%'v2.3')
    # # aser_events=dict([(text_id, info['aser']) for text_id, info in aser.items()])
    # # sentences = dict([(text_id, info['sentences']) for text_id, info in aser.items()])
    # # joblib.dump((aser_events[text_id], sentences[text_id]), 'Data/debug_textID_%d_dataset'%text_id)
    #
    # aser_events, sentences = joblib.load('Data/debug_textID_%d_dataset'%text_id)
    # event_restore_map,_,_=restore_event(text_id, sentences, aser_events, personal_pronoun, conjugator)
    # res=Engine.debug_aser_process(aser_events, belief, event_restore_map[text_id], aser_setting)
    # with open("Data/debug_textID_%d_experience.v3.02"%text_id, "wb") as outfile:
    #    pickle.dump(res, outfile)

    # ------------ batch debug ------------- #
    test_aser,test_restore=joblib.load('Data/amazon_food_review_aser_event_restore_testset100.v2')
    res={}
    for text_id, info in test_aser.items():
        res[text_id]=Engine.debug_aser_process(info['aser'], belief, test_restore[text_id], aser_setting)
    with open("Data/debug_testset100_v2_experience.v3.11", "wb") as outfile:
        pickle.dump(res, outfile)

    exit(0)