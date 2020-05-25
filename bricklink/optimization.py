import math
import sys

from ortools.linear_solver import pywraplp

from models import Listing, Part, Store


class RarePartError(Exception):

    def __init__(self, part):
        self.part = part


def pre_optimize(parts, listings, stores, min_listings):
    '''
    Apply heuristics for reducing the optimization space
    '''
    store_listing_number = {}
    for listing in listings:
        if listing.store_id not in store_listing_number:
            store_listing_number[listing.store_id] = set()
        store_listing_number[listing.store_id].add('{}-{}'.format(listing.element_id, listing.color_id))

    filtered_store_ids = set()
    for store_id, part_ids in store_listing_number.items():
        if len(part_ids) >= min_listings:
            filtered_store_ids.add(store_id)

    filtered_listings = []
    for listing in listings:
        if listing.store_id in filtered_store_ids:
            filtered_listings.append(listing)

    filtered_stores = []
    for store in stores:
        if store.store_id in filtered_store_ids:
            filtered_stores.append(store)

    part_store = {}
    part_ids = set()
    for listing in filtered_listings:
        key = '{}-{}-{}'.format(listing.element_id, listing.color_id, listing.store_id)
        part_ids.add(listing.element_id)
        if key not in part_store:
            part_store[key] = [listing, 0]
        part_store[key][1] += listing.qty

    aggregated_listings = []
    for _, val in part_store.items():
        listing, qty = val
        listing.qty = qty
        aggregated_listings.append(listing)

    filtered_parts = []
    for part in parts:
        if part.element_id in part_ids:
            filtered_parts.append(part)
        else:
            raise RarePartError(part)

    print('parts {} -> {}'.format(len(parts), len(filtered_parts)))
    print('listings {} -> {}'.format(len(listings), len(aggregated_listings)))
    print('stores {} -> {}'.format(len(stores), len(filtered_stores)))
    return filtered_parts, aggregated_listings, filtered_stores


def optimize(parts, listings, stores, shipping_costs):
    solver = pywraplp.Solver('lego_mip_optimization', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    solver_params = pywraplp.MPSolverParameters()
    solver.EnableOutput()
    infinity = solver.infinity()

    vars_part_listing = []
    vars_store = []

    # Variable - part listings
    for pi in range(len(parts)):
        for li in range(len(listings)):
            if parts[pi].element_id == listings[li].element_id and parts[pi].color_id == listings[li].color_id:
                var = solver.IntVar(0.0, infinity, '{}-{}'.format(pi, li))
                vars_part_listing.append(var)
            else:
                vars_part_listing.append(None)

    # Variable - stores
    for si in range(len(stores)):
        var = solver.IntVar(0.0, 1.0, 'store-{}'.format(si))
        vars_store.append(var)

    print('Number of variables', solver.NumVariables())

    # Constraint - calculate the number of stores
    for si in range(len(stores)):
        for li in range(len(listings)):
            if listings[li].store_id != stores[si].store_id:
                continue
            for pi in range(len(parts)):
                if not(parts[pi].element_id == listings[li].element_id and parts[pi].color_id == listings[li].color_id):
                    continue
                index = to_var_index(parts, listings, pi, li)
                solver.Add(vars_part_listing[index] <= vars_store[si] * 10000)

    # Constraint - minimum quantity for parts
    for pi, part in enumerate(parts):
        sum = None
        for li in range(len(listings)):
            if not(parts[pi].element_id == listings[li].element_id and parts[pi].color_id == listings[li].color_id):
                continue
            index = to_var_index(parts, listings, pi, li)
            if sum is None:
                sum = vars_part_listing[index]
            else:
                sum += vars_part_listing[index]
        if sum:
            solver.Add(sum >= part.qty)

    # We don't need this anymore since we decreased the number of variables
    # # Constraint - listings are associated with corresponding parts
    # for pi, part in enumerate(parts):
    #     for li, listing in enumerate(listings):
    #         if part.element_id != listing.element_id or part.color_id != listing.color_id:
    #             index = to_var_index(parts, listings, pi, li)
    #             solver.Add(vars_part_listing[index] == 0)

    # # Constraint - dont buy more than the max quantity of the vendor
    # for pi in range(len(parts)):
    #     for li, listing in enumerate(listings):
    #         if part.element_id != listing.element_id or part.color_id != listing.color_id:
    #             index = to_var_index(parts, listings, pi, li)
    #             solver.Add(vars[index] == 0)

    # # Constraint - limited number of stores
    # sum = None
    # for si in range(len(stores)):
    #     if sum is None:
    #         sum = vars_store[si]
    #     else:
    #         sum += vars_store[si]
    # solver.Add(sum <= 20)
    

    # Objective - minimize price
    sum = None
    for pi, part in enumerate(parts):
        for li, listing in enumerate(listings):
            if not(parts[pi].element_id == listings[li].element_id and parts[pi].color_id == listings[li].color_id):
                continue
            index = to_var_index(parts, listings, pi, li)
            if not listing.price > 0:
                print('unrealistic price warning', listing.price)
            if sum is None:
                sum = vars_part_listing[index] * listing.price
            else:
                sum += vars_part_listing[index] * listing.price

    print('Number of constraints', solver.NumConstraints())

    # Objective - minimize stores
    for si in range(len(stores)):
        if sum is None:
            sum = vars_store[si] * shipping_costs
        else:
            sum += vars_store[si] * shipping_costs

    solver.Minimize(sum)

    status = solver.Solve(solver_params)

    optimal_listings = []
    if status == pywraplp.Solver.OPTIMAL:
        for pi in range(len(parts)):
            sys.stdout.write('{}'.format(parts[pi]))
            for li in range(len(listings)):
                if parts[pi].element_id == listings[li].element_id and parts[pi].color_id == listings[li].color_id:
                    solution = vars_part_listing[to_var_index(parts, listings, pi, li)].solution_value()
                    if solution > 0:
                        sys.stdout.write(' {}'.format(listings[li]))
                        optimal_listings.append(listings[li])
            print('')
        # for si in range(len(stores)):
        #     print(stores[si].store_id, vars_store[si].solution_value())
        print('Solution:')
        print('Objective value =', solver.Objective().Value())
    else:
        print('The problem does not have an optimal solution.')
    
    return optimal_listings


def to_var_index(parts, listings, part_index, listing_index):
    return len(listings) * part_index + listing_index


def to_listing_index(parts, listings, var_index):
    return math.floor(var_index / len(parts))


def to_part_index(parts, listings, var_index):
    return var_index % len(parts)


if __name__ == '__main__':
    parts = [
        Part(3010,1,10),
        Part(3011,1,6),
    ]
    listings = [
        Listing(3010,1,10,0.1,'','', 's1', 301000),
        Listing(3011,1,10,0.1,'','', 's2', 301100)
    ]
    stores = [
        Store('s1'),
        Store('s2')
    ]
    optimize(parts, listings, stores)
