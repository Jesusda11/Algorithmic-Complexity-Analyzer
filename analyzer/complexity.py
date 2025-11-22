def analyze_complexity(structure):
    """
    Versión ultrabásica:
    - Solo maneja 1 bucle FOR.
    - Devuelve O(n).
    """

    if not structure:
        return "O(1)"

    node = structure[0]

    if node["type"] == "for":
        iterations = node["iterations"]

        # Por ahora asumimos que iteraciones = n
        return f"O({iterations})"

    return "O(1)"
