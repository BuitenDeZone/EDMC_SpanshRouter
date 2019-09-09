#! /usr/bin/env python2

import os
import csv
import json
from pprint import pprint as pp
# Saved route file. Stored in the plugin dir.

class RouteManager():
    """
    Portrayes a CSV file.
    """

    ROUTE_FILE = 'route.csv'

    # "System Name","Distance To Arrival","Distance Remaining","Neutron Star","Jumps"
    FIELD_SYSTEMNAME = 0
    FIELD_DISTANCE_ARRIVAL = 1
    FIELD_DISTANCE_REMAINING = 2
    FIELD_IS_NEUTRON = 3
    FIELD_JUMPS = 4
    # the saved offset field should always be the last column (if ever adding new ones)
    FIELD_SAVED_OFFSET = 5

    JSON_FIELDS_SYSTEM = "system"
    JSON_FIELDS_DISTANCE_ARRIVAL = "distance_jumped"
    JSON_FIELDS_DISTANCE_REMAINING = "distance_left"
    JSON_FIELDS_IS_NEUTRON = "neutron_star"
    JSON_FIELDS_JUMPS = "jumps"

    def __init__(self, plugin_dir):
        self.offset = 0
        self.route = []
        self.route_file = os.path.join(plugin_dir, self.ROUTE_FILE)

        self.c_total_jumps = None
        self.c_total_jumps_left = None

        # Load last known route if file exists.
        if os.path.exists(self.route_file):
            self.load_saved_route()

    def load_json_spansh(self, json_payload):
        self.offset = 0
        self.route = []
        system_jumps = json.loads(json_payload)["result"]["system_jumps"]
        for waypoint in system_jumps:
            self.route.append([
                waypoint[self.JSON_FIELDS_SYSTEM],
                waypoint[self.JSON_FIELDS_DISTANCE_ARRIVAL],
                waypoint[self.JSON_FIELDS_DISTANCE_REMAINING],
                waypoint[self.JSON_FIELDS_IS_NEUTRON],
                waypoint[self.JSON_FIELDS_JUMPS],
            ])

    def load_saved_route(self):
        # Saved file format is spansh format without header.
        self.load_file_spansh(self.route_file, False)

    def load_file_spansh(self, filename, strip_header=True):
        self.offset = 0
        self.route = []
        try:
            with open(filename, 'r') as csvfile:
                route_reader = csv.reader(csvfile)
                if strip_header:
                    route_reader.next()
                current_row = 0
                for row in route_reader:
                    if row not in (None, "", []):
                        if row.__len__() > (self.FIELD_JUMPS + 1):
                            if row[self.FIELD_SAVED_OFFSET] == 'Current':
                              self.offset = current_row
                            del row[self.FIELD_SAVED_OFFSET]

                        self.route.append(row[0:self.FIELD_SAVED_OFFSET])
                    current_row += 1
        except:
            print("Unable to load file %s".format(filename))

    def current_offset(self):
        return self.offset

    def current_row(self):
        return self.route[self.offset]

    def current_destination(self):
        return self.current_row()[self.FIELD_SYSTEMNAME]

    def current_remaining(self):
        return float(self.current_row()[self.FIELD_DISTANCE_REMAINING])

    def current_distance_to_arrival(self):
        return float(self.current_row()[self.FIELD_DISTANCE_ARRIVAL])

    def current_jumps(self):
        return int(self.current_row()[self.FIELD_JUMPS])

    def targets_left(self):
        return max([self.route.__len__() - self.offset, 0])

    def next_target(self):
        if self.targets_left() > 0:
            self.c_total_jumps_left = None
            self.offset += 1

    def prev_target(self):
        if self.offset > 0:
            self.c_total_jumps_left = None
            self.offset -= 1

    def get_total_left_with_units(self):
        """
        Returns total left distance with a unit as a tuple.
        """

        total_left = self.current_remaining()
        total_left_unit = 'Ly'
        if total_left > 1000.0:
            total_left_unit = 'kLy'
            total_left = total_left / 1000

        return round(total_left, 1), total_left_unit

    def total_jumps(self):
        if self.c_total_jumps is None:
            self.c_total_jumps = sum([int(row[self.FIELD_JUMPS]) for row in self.route[:]])
        return self.c_total_jumps

    def total_jumps_left(self):
        if self.c_total_jumps_left is None:
            if self.route.__len__() == 0 or self.targets_left() == 0:
                self.c_total_jumps_left = 0
            else:
                self.c_total_jumps_left = sum([int(row[self.FIELD_JUMPS]) for row in self.route[self.offset:]])

        return self.c_total_jumps_left

    def clear(self):
        self.route = []
        self.offset = 0
        self.c_total_jumps = None
        self.c_total_jumps_left = None
        if os.path.exists(self.route_file):
            try:
                os.remove(self.route_file)
            except:
                print("Unable to remove route file: %s".format(self.route_file))

    def write_route(self):
        if self.route.__len__() != 0:
            current_row = 0
            with open(self.route_file, 'w') as csvfile:
                writer = csv.writer(csvfile)
                for row in self.route:
                    # Cut off any unknown columns
                    row = row[0:self.FIELD_SAVED_OFFSET]
                    if self.offset == current_row:
                       row.append("Current")
                    writer.writerow(row)
                    current_row += 1
        else:
            self.clear()

    def __len__(self):
        return self.route.__len__()