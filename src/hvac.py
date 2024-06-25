def get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts: int or None,
                                                         max_consumed_electric_cooling_kilowatts: int or None) -> dict:
    if max_consumed_electric_heating_kilowatts and max_consumed_electric_cooling_kilowatts:
        raise ValueError('Too much inputs. Input only one: max_consumed_electric_heating_kilowatts or '
                         'max_consumed_electric_cooling_kilowatts')

    if max_consumed_electric_heating_kilowatts:
        hvac_consumed_electric_active_power_in_kilowatts = max_consumed_electric_heating_kilowatts
        label = 'HVAC_heating'
    elif max_consumed_electric_cooling_kilowatts:
        hvac_consumed_electric_active_power_in_kilowatts = max_consumed_electric_cooling_kilowatts
        label = 'HVAC_cooling'
    else:
        raise ValueError('max_consumed_electric_heating_kilowatts and max_consumed_electric_cooling_kilowatts are None')

    return {label: hvac_consumed_electric_active_power_in_kilowatts}
