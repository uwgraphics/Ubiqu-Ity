__author__ = 'zthomae'

from BeautifulSoup import BeautifulStoneSoup


def read_text(annotated_text):
    """Turns a string representation of an XML tree into a list of tags with their LATs
    """
    tags = []
    text_tree = BeautifulStoneSoup(annotated_text)
    for a in text_tree('a'):
        tags.append({
            'lat': a['lat'],
            'tag': a.text
        })
    return tags


def compare_results(t1, t2):
    """Creates and returns a dictionary structure with summary information on the differences
    between the taggings in the two documents
    """
    results = {}

    t1_tags = read_text(t1)
    t2_tags = read_text(t2)
    t1_lats = count_lats(t1_tags)
    t2_lats = count_lats(t2_tags)
    lats = set().union(t1_lats.keys(), t2_lats.keys())

    # calculate percent accuracy
    count_total = 0
    count_incorrect = 0
    for lat in lats:
        if lat in t1_lats:
            t1_count = t1_lats[lat]
        else:
            t1_count = 0
        if lat in t2_lats:
            t2_count = t2_lats[lat]
        else:
            t2_count = 0
        if t1_count == t2_count:
            count_total += t1_count
        else:
            count_total += max(t1_count, t2_count)
            count_incorrect += abs(t1_count - t2_count)

    results['count_correct'] = count_total - count_incorrect
    results['count_incorrect'] = count_incorrect
    results['pct_accuracy'] = 1.0 - (count_incorrect / float(count_total))

    results['t1_lats'] = t1_lats
    results['t2_lats'] = t2_lats
    results['t1_count'] = sum(v for v in t1_lats.values())
    results['t2_count'] = sum(v for v in t2_lats.values())

    # TODO: Other results

    return results


def count_lats(tags):
    """This counts the number of times each LAT appears in the tags. Compared for grading"""
    counts = {}
    for t in tags:
        if t['lat'] not in counts:
            counts[t['lat']] = 1
        else:
            counts[t['lat']] += 1
    return counts