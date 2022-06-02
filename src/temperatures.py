def check_initial_inside_degree_celsius(initial_inside_degree_celsius: float,
                                        max_inside_degree_celsius: float, min_inside_degree_celsius: float) -> bool:
    if min_inside_degree_celsius <= initial_inside_degree_celsius <= max_inside_degree_celsius:
        return True
    else:
        raise ValueError(
            'The current initial_inside_degree_celsius of {} is out of the range between the '
            'min_inside_degree_celsius ({}) and max_inside_degree_celsius ({})'.format(initial_inside_degree_celsius,
                                                                                       min_inside_degree_celsius,
                                                                                       max_inside_degree_celsius))
