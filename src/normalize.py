from itertools import groupby

# DEEPGRAM KEY WORDS
META = "metadata"
RES = "results"
CHA = "channels"
ALT = "alternatives"
WORDS = "words"
WORD = "word"
START = "start"
END = "end"
CONF = "confidence"
PUNCT = "punctuated_word"
SPEAKER = "speaker"


class Options:
    def __init__(self, opt):
        self.channel_map = opt['channel_map']


class Word:
    def __init__(self, word, index):
        self.word_text = word[PUNCT]
        self.word_index = index
        self.confidence = word[CONF]
        self.start_time = word[START]
        self.end_time = word[END]
        self.channel_index = word["channel_index"]
        self.speaker_index = word["speaker_index"]


class Turn:
    def __init__(self, turn, source, index):
        self.words_array = [Word(word=word, index=index+1)
                            for index, word in enumerate(turn)]
        self.turn_index = index
        self.channel_index = self.words_array[0].channel_index
        self.speaker_index = self.words_array[0].speaker_index
        self.turn_text = ' '.join(
            [word.word_text for word in self.words_array])
        self.start_time = self.words_array[0].start_time
        self.end_time = self.words_array[-1].end_time
        self.source = source


class Transcript:
    def __init__(self, transcript, options):
        self.options = options
        self.metadata = transcript[META]

        dg_words = []
        for index, channel in enumerate(transcript[RES][CHA]):
            new_words=[]
            speaker_in_channel_count=len(set(word[SPEAKER] for word in channel[ALT][0][WORDS] if SPEAKER in word))
            
            for word in channel[ALT][0][WORDS]:
                channel_count=len(transcript[RES][CHA])
                channel_index=index
                speaker_in_channel_index = word[SPEAKER] if SPEAKER in word else None
                
                try:
                    if speaker_in_channel_index: # Diarized
                        if isinstance(options.channel_map[channel_index], list):
                            speaker_name=options.channel_map[channel_index][speaker_in_channel_index] # Agent / Supervisor / Caller
                        elif isinstance(options.channel_map[channel_index], str):
                            speaker_name=options.channel_map[channel_index]+'_'+str(speaker_in_channel_index+1) # Agent_1 / Agent_2 / Caller_1
                        else:
                            raise IndexError
                    else: # Standard
                        if isinstance(options.channel_map[channel_index], list):
                            speaker_name=options.channel_map[channel_index][0] # Agent / Supervisor / Caller
                        elif isinstance(options.channel_map[channel_index], str):
                            speaker_name=options.channel_map[channel_index] # Agent / Caller
                        else:
                            raise IndexError
                except IndexError:
                    speaker_name='unknown_'+str(channel_index+1)+(str('_'+speaker_in_channel_index+1) if speaker_in_channel_index else '') # unknown_1_3
                
                new_word={**word, SPEAKER: speaker_name, 
                          "channel_index":channel_index, 
                          "speaker_index":speaker_in_channel_index if speaker_in_channel_index else 0}
                new_words.append(new_word)
            dg_words.extend(new_words)
            
        dg_words.sort(key=lambda word: (word[START], word[END], word[SPEAKER]))

        # words_split_by_turn = [list(turn) for key, turn in groupby(
        #     dg_words, lambda word: word[SPEAKER])]
        words_split_by_turn = [list(turn) for key, turn in groupby(
            dg_words, lambda word: str(word["channel_index"])+'_'+str(word["speaker_index"]))]

        self.turns_array = [Turn(
            turn=turn,
            source=turn[0][SPEAKER], # type: ignore
            index=ind+1,
        ) for ind, turn in enumerate(words_split_by_turn)]

    def toJson(self):
        return {
            "metadata": {
                **self.metadata,
                "media": {
                    "media_type": "voice",
                    "external_id": ""
                },
                # "speaker_names": [name for channel,name in sorted(self.options.channel_map.items(), key=lambda x: x[0]) ]
                "speaker_names": self.options.channel_map
            },
            "turns_array": [
                {"turn_index": turn.turn_index,
                 "turn_text": turn.turn_text,
                 "source": turn.source,
                 "channel_index": turn.channel_index,
                 "source_index": turn.speaker_index,
                 "start_time": turn.start_time,
                 "end_time": turn.end_time,
                 "words_array": [
                     {"word_index": word.word_index,
                      "word_text": word.word_text,
                      "confidence": word.confidence,
                      "start_time": word.start_time,
                      "end_time": word.end_time}
                     for word in turn.words_array]}
                for turn in self.turns_array]}

def normalise_deepgram(deepgram_transcript, options):
    opts = Options(options)
    return Transcript(deepgram_transcript, opts).toJson()
