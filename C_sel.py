def get_ambient_temp_constant(ambient_temp_celsius):
    """
    Returns the ambient temperature constant based on NEC rules.

    """
    if ambient_temp_celsius < 50:

        return 0.82
    else:
        return 0.76

def calculate_mca(load_current_amps, ambient_temp_celsius):
    """
    Calculates the Minimum Cable Ampacity (MCA).
    
    Parameters:
    - load_current_amps: Load current in Amperes
    - ambient_temp_celsius: Ambient temperature in Celsius

    Returns:
    - Minimum Cable Ampacity (float)
    """
    ambient_temp_constant = get_ambient_temp_constant(ambient_temp_celsius)
    safety_factor = 1.25
    mca = (safety_factor * load_current_amps) / ambient_temp_constant
    return mca

# Example usage
if __name__ == "__main__":
    # Sample inputs
    ambient_temp = float(input("Enter ambient temperature in °C: "))
    load_current = float(input("Enter load current in Amperes (A): "))

    mca = calculate_mca(load_current, ambient_temp)

    print(f"\nMinimum Cable Ampacity (MCA) needed: {mca:.2f} A")




