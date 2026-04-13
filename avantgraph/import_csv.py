#!/usr/bin/env python3
"""
Tool to convert csv files into a format AvantGraph understands. The output can
be piped directly into AvantGraph for loading.

Example: ag-load-graph --graph-format=json <(python3 import_csv.py opts...) graphDir/
"""
import click
import csv
import enum
import json
import sys

class CSVConfig:
    def __init__(self, separator, quoting, escape_char):
        self.separator = separator
        self.quoting = quoting
        self.escape_char = escape_char

    def open(self, file):
        return csv.reader(
                file,
                delimiter=self.separator,
                skipinitialspace=True,
                quoting=self.quoting,
                escapechar=self.escape_char)

class ColumnType(enum.Enum):
    # Ignore column
    IGNORE = 0

    # Output as
    BOOL = 1
    NUMBER = 2
    STRING = 3

    # Cross reference
    ID = 4
    START_ID = 5
    END_ID = 6

_COLUMN_TYPE_NAMES = {
    "IGNORE": ColumnType.IGNORE,

    "BOOL": ColumnType.BOOL,
    "DOUBLE": ColumnType.NUMBER,
    "FLOAT": ColumnType.NUMBER,
    "STRING": ColumnType.STRING,
    "LONG": ColumnType.NUMBER,
    "INT": ColumnType.NUMBER,
    "INTEGER": ColumnType.NUMBER,

    "ID": ColumnType.ID,
    "START_ID": ColumnType.START_ID,
    "END_ID": ColumnType.END_ID,
}

class ParseException(Exception):
    pass

class Column:
    def __init__(self, name, type, namespace):
        self.name = name
        self.type = type
        self.namespace = namespace

    @staticmethod
    def parse(field):
        parts = field.split(":")
        if len(parts) != 2:
            raise ParseException("Field header %s should contain exactly one : separating the name from the type"
                    % field)

        name, type_descr = parts[0], parts[1]
        if "(" in type_descr:
            type_descr, namespace = type_descr.split("(", 2)
            namespace = namespace[:-1]
        else:
            namespace = None

        type = _COLUMN_TYPE_NAMES.get(type_descr)
        if not type:
            raise ParseException(
                    "Invalid type name: %s (in %s)" % (type_descr, field))
        elif namespace is not None \
                and type not in (ColumnType.ID, ColumnType.START_ID, ColumnType.END_ID):
            raise ParseException(
                    "Column type %s should not have a namespace (in %s)" % (type, field))
        elif not name \
                and type not in (ColumnType.ID, ColumnType.START_ID, ColumnType.END_ID):
            raise ParseException(
                    "Column type %s should have a name (in %s)" % (type, field))
        elif namespace is not None and not namespace:
            raise Exception(
                    "Invalid namespace: %s (in %s)" % (namespace, field))

        return Column(name, type, namespace)

class InputFile:
    def __init__(self, csv, file_name, labels):
        self.file_name = file_name
        self.labels = labels
        self.file = open(file_name, "r")

        # Count size
        self.expected_count = sum(1 for line in self.file)
        self.file.seek(0)

        self.reader = csv.open(self.file)
        self.cols = []
        self._parse_header()

    def _parse_header(self):
        header = next(self.reader)
        for idx, field in enumerate(header):
            self.cols.append(Column.parse(field))

class NodeInput(InputFile):
    def __init__(self, csv, file_name, labels):
        super().__init__(csv, file_name, labels)

        self._id_col = None
        self._id_col_idx = -1
        for i, col in enumerate(self.cols):
            if col.type == ColumnType.ID:
                if self._id_col:
                    raise ParseException("Multiple id columns")

                self._id_col = col
                self._id_col_idx = i
            elif col.type in (ColumnType.START_ID, ColumnType.END_ID):
                raise ParseException("Cannot have start/end column in node: %s" % col)

    @property
    def id_col(self):
        return self._id_col

    def process(self, next_id, namespace_key_to_id):
        labels = ("\"" + "\", \"".join(self.labels) + "\"") if self.labels else ""
        tpl = "{\"type\":\"node\",\"id\":\"%d\",\"labels\":[" + labels + "],\"properties\":{%s}}"

        if self._id_col.namespace:
            idmap = namespace_key_to_id.get(self._id_col.namespace)
            if not idmap:
                idmap = {}
                namespace_key_to_id[self._id_col.namespace] = idmap
        else:
            idmap = None

        with click.progressbar(self.reader, length=self.expected_count, label=self.file_name, file=sys.stderr) as reader:
            for row in reader:
                if idmap is not None:
                    idmap[int(row[self._id_col_idx])] = next_id
                print (tpl % (next_id, ""))
                next_id += 1
        return next_id

class RelationInput(InputFile):
    def __init__(self, csv, file_name, labels):
        super().__init__(csv, file_name, labels)

        self.start_labels = []
        self.end_labels = []

        self._start_col = None
        self._end_col = None
        self._start_col_idx = -1
        self._end_col_idx = -1

        _id_col = None
        for i, col in enumerate(self.cols):
            if col.type == ColumnType.ID:
                if _id_col:
                    raise ParseException("Multiple id columns")

                _id_col = col
            elif col.type == ColumnType.START_ID:
                if self._start_col:
                    raise ParseException("Multiple start id columns")

                self._start_col = col
                self._start_col_idx = i
            elif col.type == ColumnType.END_ID:
                if self._end_col:
                    raise ParseException("Multiple end id columns")

                self._end_col = col
                self._end_col_idx = i

    @property
    def start_col(self):
        return self._start_col
    @property
    def end_col(self):
        return self._end_col

    def process(self, next_id, namespace_key_to_id):
        edge_label = json.dumps(str(self.labels[0]))
        start_labels = json.dumps(self.start_labels)
        end_labels = json.dumps(self.end_labels)

        # Escape
        edge_label = edge_label.replace("%", "%%")
        start_labels = start_labels.replace("%", "%%")
        end_labels = end_labels.replace("%", "%%")

        tpl = "{\"type\":\"relationship\", \"id\":\"%d\", " \
                + "\"label\": " + edge_label + ", " \
                + "\"start\": {\"id\": \"%d\", \"labels\": " + start_labels + "}, " \
                + "\"end\": {\"id\": \"%d\", \"labels\": " + end_labels + "}, " \
                + "\"properties\":{%s}}"

        start_ids = namespace_key_to_id[self._start_col.namespace]
        end_ids = namespace_key_to_id[self._end_col.namespace]

        with click.progressbar(self.reader, length=self.expected_count, label=self.file_name, file=sys.stderr) as reader:
            for row in reader:
                start = int(row[self._start_col_idx])
                end = int(row[self._end_col_idx])

                start_id = start_ids.get(start)
                end_id = end_ids.get(end)

                if start_id is None:
                    print("Missing start id %d in namespace %s for %s" % (start, self._start_col.namespace, row), file=sys.stderr)
                if end_id is None:
                    print("Missing end id %d in namespace %s for %s" % (end, self._end_col.namespace, row), file=sys.stderr)
                if start_id is not None and end_id is not None:
                    print (tpl % (next_id, start_id, end_id, ""))
                    next_id += 1
        return next_id

def _parse_label_file_pair(n):
    parts = n.split("=", 2)
    if len(parts) == 1:
        return "", parts[0]
    else:
        return parts[0].split(":"), parts[1]

@click.command()
@click.option("--nodes", multiple=True, help="A label followed by an '=' character and a file name to import nodes for")
@click.option("--relationships", multiple=True, help="A label followed by an '=' character and a file name to import relationships for")
@click.option("--delimiter", default=",", help="The field separator in the CSV files")
@click.option('--escapechar', default=None, help="The character to use for escaping in CSV files")
def main(nodes, relationships, delimiter, escapechar):
    csv = CSVConfig(delimiter, 0, escapechar)

    id_namespace_to_labels = {}
    node_files = []
    for f in nodes:
        labels, file_name = _parse_label_file_pair(f)
        try:
            input = NodeInput(csv, file_name, labels)
        except ParseException as e:
            print ("Failed to parse header of %s: %s" % (file_name, e), file=sys.stderr)
            return

        node_files.append(input)

        if input.id_col:
            id_namespace_to_labels[input.id_col.namespace] = labels

    relation_files = []
    for f in relationships:
        labels, file_name = _parse_label_file_pair(f)
        try:
            input = RelationInput(csv, file_name, labels)
            if input.start_col.namespace not in id_namespace_to_labels:
                raise ParseException(
                        "Don't have an input with namespace %s" % input.start_col.namespace)
            if input.end_col.namespace not in id_namespace_to_labels:
                raise ParseException(
                        "Don't have an input with namespace %s" % input.end_col.namespace)
        except ParseException as e:
            print ("Failed to parse header of %s: %s" % (file_name, e), file=sys.stderr)
            return

        input.start_labels = id_namespace_to_labels[input.start_col.namespace]
        input.end_labels = id_namespace_to_labels[input.end_col.namespace]

        relation_files.append(input)

    next_id = 0
    namespace_key_to_id = {}
    for node in node_files:
        next_id = node.process(next_id, namespace_key_to_id)
    for relation in relation_files:
        next_id = relation.process(next_id, namespace_key_to_id)

main()
