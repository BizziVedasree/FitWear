def classify_body_shape(bust, waist, high_hip, hip):
    bust_hips_diff = abs(bust - hip)
    hips_bust_diff = abs(hip - bust)
    bust_waist_diff = bust - waist
    hips_waist_diff = hip - waist

    # Hourglass: Bust and hips should be close in size, with a well-defined waist
    if (bust_hips_diff <= 2 and hips_bust_diff <= 2 and bust_waist_diff >= 9 and hips_waist_diff >= 10):
        return "Hourglass"
    
    # Triangle (Pear): Hips significantly larger than bust, but waist is still defined
    elif (hips_bust_diff > 3.6 and hips_waist_diff >= 9):
        return "Triangle"
    
    # Inverted Triangle: Bust significantly larger than hips, but with a defined waist
    elif (bust_hips_diff > 3.6 and bust_waist_diff >= 9 and hips_waist_diff < 9):
        return "Inverted Triangle"
    
    # Apple: Waist is close to bust and hips, or waist is larger than or equal to one of them
    elif (bust_waist_diff < 5 and hips_waist_diff <= 10) or (waist >= bust or waist >= hip):
        return "Apple"
    
    # Rectangle: No significant difference between bust, waist, and hips
    elif (hips_bust_diff <= 3.6 and bust_hips_diff <= 3.6 and bust_waist_diff < 9 and hips_waist_diff < 10):
        return "Rectangle"
    
    else:
        return "Shape not classified"

    