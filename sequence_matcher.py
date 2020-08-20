class SequenceMatcher:
    def __init__(self, first_sentence, second_sentence, execute_immediately=False):
        self.first_sentence = first_sentence.strip().lower()
        self.second_sentence = second_sentence.strip().lower()
        self.min_word_size = 3
        self.subtoken_length = 2
        self.threshold_word = 0.45
        self.threshold_sentence = 0.27
        if execute_immediately:
            self()

    def __normalize_sentence(self, sentence):
        res = ''
        for i in sentence:
            if i.isalnum() or i == ' ':
                res += i
        return res

    def __get_tokens(self, sentence):
        res = []
        for i in sentence.split():
            if len(i) >= self.min_word_size:
                res.append(i)
        return res

    def __is_token_fuzzy_equal(self, token1, token2):
        count = 0
        used_tokens = [False] * (len(token2) - self.subtoken_length + 1)
        for i in range(len(token1) - self.subtoken_length + 1):
            subtoken_first = token1[i:self.subtoken_length]
            for j in range(len(token2) - self.subtoken_length + 1):
                if not used_tokens[j]:
                    subtoken_second = token2[j:self.subtoken_length]
                    if subtoken_first == subtoken_second:
                        count += 1
                        used_tokens[j] = True
                        break

        subtoken_first_count = len(token1) - self.subtoken_length + 1
        subtoken_second_count = len(token2) - self.subtoken_length + 1
        tanimoto = count / (subtoken_first_count + subtoken_second_count - count)
        return self.threshold_word <= tanimoto

    def __get_fuzzy_equals_token(self, tokens1, tokens2):
        equals_tokens = []
        used_token = [False] * len(tokens2)
        for i in range(len(tokens1)):
            for j in range(len(tokens2)):
                if not used_token[j]:
                    if self.__is_token_fuzzy_equal(tokens1[i], tokens2[j]):
                        equals_tokens.append(tokens1[i])
                        used_token[j] = True
                        break

        return equals_tokens

    def __calculate_fuzzy_equal_value(self, first, second):
        if not (first.strip() or second.strip()):
            return 1.0
        if not (first.strip() and second.strip()):
            return 0.0
        normalized_first = self.__normalize_sentence(first)
        normalized_second = self.__normalize_sentence(second)

        tokens_first = self.__get_tokens(normalized_first)
        tokens_second = self.__get_tokens(normalized_second)

        fuzzy_equals_token = self.__get_fuzzy_equals_token(tokens_first, tokens_second)

        count = len(fuzzy_equals_token)
        first_count = len(tokens_first)
        second_count = len(tokens_second)

        res = count / (first_count + second_count - count)

        return res >= self.threshold_sentence

    def __call__(self, *args, **kwargs):
        if not hasattr(self, 'res'):
            self.res = self.__calculate_fuzzy_equal_value(self.first_sentence, self.second_sentence)
        return self.res


if __name__ == '__main__':
    str1 = 'Петров Иван'
    str2 = 'петр'
    print(SequenceMatcher(str1, str2)())
