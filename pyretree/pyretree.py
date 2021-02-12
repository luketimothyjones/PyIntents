import re
import pprint
from operator import itemgetter

# --- Logging configuration
import logging
pyretree_logger = logging.getLogger(__name__)
pyretree_logger.addHandler(logging.NullHandler())
# ---


class _RegexTree:

    def __init__(self, separator=' ', preserve_regexps=False, max_depth=None):
        self._raw_regexps = []
        self._tree = {}

        self._separator = separator
        self._preserve_regexps = preserve_regexps
        self._max_depth = max_depth
        self._built = False

        self._pending_count = 0
        self._regex_count = 0

        self._regex_flags = re.IGNORECASE
        self._build_parser_main = re.compile('<(.*?)(=(.*?))?>', flags=self._regex_flags)
        self._build_parser_fill_novalue = re.compile('>\)', flags=self._regex_flags)

    # ----
    def add(self, expression, callback):
        if self._built and not self._preserve_regexps:
            return False

        self._built = False
        self._raw_regexps.append((expression, self._build_regex(expression), callback))
        self._pending_count += 1

        return True

    # ----
    def build_tree(self):
        if self._built:
            return False

        if self._max_depth is None:
            self._max_depth = max(1, self._regex_count // 5)

        else:
            if self._max_depth < 1:
                pyretree_logger.debug('Max depth must be at least 1; defaulting to 1\n')
                self._max_depth = 1

        # Counters are incremented/decremented for debugging purposes
        if self._preserve_regexps:
            self._regex_count = 0

            for regex in reversed(self._raw_regexps):
                self._add_to_tree(regex)
                self._regex_count  += 1

        else:
            while self._raw_regexps:
                self._add_to_tree(self._raw_regexps.pop())
                self._regex_count  += 1
                self._pending_count -= 1

        self._built = True
        return True

    # ----
    def _build_regex(self, expression, raw=False):
        if raw:
            return re.compile(expression, flags=self._regex_flags)

        # Replace name/value shorthand with proper regex syntax
        parsed = self._build_parser_main.sub(r'(?P<\1>\3)', expression)
        parsed = self._build_parser_fill_novalue.sub(r'>.*?)', parsed)

        return re.compile(f'^{parsed}$', flags=self._regex_flags)

    # ----  
    def _add_to_tree(self, regex):
        expression, regex, callback = regex

        current_node = self._tree
        expression_parts = expression.split(self._separator)
        parts_count = len(expression_parts)

        max_depth = min(self._max_depth, parts_count)

        # Iterate through the expression and build the branches
        for part_pos in range(max_depth):
            part = expression_parts[part_pos]

            # Hit a variable (<...>)
            if part[0] == '<' and part[-1] == '>':
                # Create an regex list if one does not exist
                current_node['<VAR>'] = current_node['<VAR>'] if '<VAR>' in current_node else []
                current_node = current_node['<VAR>']
                break

            # Hit a constant (plain text)
            else:
                if not current_node.get(part, False):
                    # Deepest node is a list
                    if part_pos == (max_depth - 1):
                        current_node[part] = []

                    # All other nodes are dicts
                    else:
                        current_node[part] = {}

            current_node = current_node[part]

        # Reached end of expression without encountering a variable
        if type(current_node) == dict:
            current_node['<END>'] = current_node['<END>'] if '<END>' in current_node else []
            current_node = current_node['<END>']

        # Expressions without variables (entirely constants) are always checked first (highest weight)
        if not '<' in expression:
            expression_weight = 9999999
        else:
            expression_weight = len(expression)

        current_node.append((expression_weight, regex, callback))
        current_node.sort(key=itemgetter(0), reverse=True)

    # ----
    def match(self, text):
        """
        Calls the most applicable regex's callback.
        --
        Returns (tuple): (bool) found match, callback result
        """

        if not self._built:
            return None

        separated = text.split(self._separator)
        first, all_but_first = separated[0], separated[1:]

        current_node = self._tree.get(first, False)

        # Text is not in regex tree
        if not current_node:
            return False, False

        if first[0] == '<' and first[-1] == '>':
            raise Exception('First item in regex cannot be a variable')

        # Traverse tree to find applicable regexps
        iter_boundry = min(len(all_but_first), self._max_depth)
        possible = []

        for word_pos in range(iter_boundry):
            word = all_but_first[word_pos]

            # TODO :: Does this limit functionality?
            if word in current_node:
                current_node = current_node[word]
                continue

            if '<VAR>' in current_node:
                possible += current_node['<VAR>']

        if '<END>' in current_node:
            possible += current_node['<END>']

        elif type(current_node) is list:
            possible += current_node

        for _, regex, callback in possible:
            extracted = regex.match(text)

            if extracted:
                return True, callback(**extracted.groupdict())

        return False, False

    # ----
    def __str__(self):
        if self._built:
            return f'<RegexTree (built) with {self._regex_count} regexps>'
        else:
            return f'<RegexTree (unbuilt) with {self._pending_count} queued regexps'

    def __repr__(self):
        if self._built:
            return pprint.pformat(self._tree)

        else:
            notice = '\n==\nNOTICE: Displaying queued regexps\n==\n' 
            return f'{notice}{pprint.pformat(self._raw_regexps)}{notice}'

# ----
class RegexCollection:
    def __init__(self, separator=' ', preserve_regexps=False):
        self._regex_tree = _RegexTree(separator=separator, preserve_regexps=preserve_reexpgs)
        self._prev_function = None

    # ----
    def add(self, expression, raw=False):

        def regex_adder(callback, *args, **kwargs):
            # Cache previous function to resolve issue with stacked decorators
            if callback is None:
                callback = self._prev_function
            self._prev_function = callback

            if not self._regex_tree.add(expression, callback):
                raise Exception('Cannot add to prepared RegexCollection when preserve_regs is False')

        return regex_adder

    # ----
    def match(self, text):
        result = self._regex_tree.match(text)

        if result is None:
            raise Exception('RegexCollection must be prepared before matching')

        return result

    # ----
    def prepare(self):
        if not self._regex_tree.build_tree():
            pyretree_logger.debug('RegexCollection was already prepared\n')

    # --------
    def __str__(self):
        if self._regex_tree._built:
            return f'<RegexCollection (built) with {self._regex_tree._regex_count} regexps>'
        else:
            return f'<RegexCollection (unbuilt) with {self._regex_tree._pending_count} unprepared regexps'

    def __repr__(self):
        if self._regex_tree._built:
            return pprint.pformat(self._regex_tree._tree)

        else:
            notice = '\n==\nNOTICE: Displaying unprepared regexps\n==\n' 
            return f'{notice}{pprint.pformat(self._regex_tree._raw_regexps)}{notice}'

    # ----
    def __len__(self):
        return self._regex_tree._regex_count if self._regex_tree._regex_count else self._regex_tree._pending_count
