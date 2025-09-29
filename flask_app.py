from flask import Flask, render_template, request, redirect, url_for, session, flash
from C_sel import calculate_mca

app = Flask(__name__)
app.secret_key = 'PetraEngineerin10318237129837912873'  # Replace with a secure key
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

@app.route('/', methods=['GET', 'POST'])
def home():
    compressors = session.get('compressors', [])
    edit_compressor = None
    edit_index = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add new compressor
            name = request.form.get('comp_name', '').strip()
            try:
                load = float(request.form.get('comp_load'))
                ambient = float(request.form.get('comp_ambient'))
                # Calculate component selection on add
                components = get_components_for_compressor(load, ambient)
                compressors.append({'name': name, 'load': load, 'ambient': ambient, 'components': components})
                session['compressors'] = compressors
                flash(f'Compressor "{name}" added.')
            except Exception:
                flash('Invalid input for compressor.')
        elif action == 'delete':
            try:
                idx = int(request.form.get('delete_index'))
                if 0 <= idx < len(compressors):
                    removed = compressors.pop(idx)
                    session['compressors'] = compressors
                    flash(f'Compressor "{removed["name"]}" deleted.')
            except Exception:
                flash('Error deleting compressor.')
        elif action == 'select':
            try:
                idx = int(request.form.get('selected_index'))
                session['selected_index'] = idx
                # Update session load/ambient to match selected compressor
                session['load_current'] = compressors[idx]['load']
                session['ambient_temp'] = compressors[idx]['ambient']
                flash(f'Selected compressor: {compressors[idx]["name"]}')
                return redirect(url_for('home'))
            except Exception:
                flash('Error selecting compressor.')
        elif action == 'edit':
            try:
                idx = int(request.form.get('edit_index'))
                if 0 <= idx < len(compressors):
                    edit_compressor = compressors[idx]
                    edit_index = idx
            except Exception:
                flash('Error loading compressor for edit.')
        elif action == 'edit_save':
            try:
                idx = int(request.form.get('edit_index'))
                name = request.form.get('comp_name', '').strip()
                load = float(request.form.get('comp_load'))
                ambient = float(request.form.get('comp_ambient'))
                components = get_components_for_compressor(load, ambient)
                compressors[idx] = {'name': name, 'load': load, 'ambient': ambient, 'components': components}
                session['compressors'] = compressors
                # If this is the selected compressor, update session values
                if session.get('selected_index') == idx:
                    session['load_current'] = load
                    session['ambient_temp'] = ambient
                flash(f'Compressor "{name}" updated.')
            except Exception:
                flash('Error updating compressor.')
        elif action == 'reset':
            session.pop('compressors', None)
            flash('All compressors have been reset.')

    return render_template('home.html', compressors=compressors, edit_compressor=edit_compressor, edit_index=edit_index)

def get_components_for_compressor(load, ambient):
    # Calculate component selection for a compressor (can be expanded)
    components = {}
    # Example: Use existing selection logic for cable, contactor, etc.
    # Cable selection (updated table)
    cable_table = [
        {"ampacity": 14, "awg": 18},
        {"ampacity": 25, "awg": 14},
        {"ampacity": 30, "awg": 12},
        {"ampacity": 40, "awg": 10},
        {"ampacity": 55, "awg": 8},
        {"ampacity": 75, "awg": 6},
        {"ampacity": 95, "awg": 4},
        {"ampacity": 110, "awg": 3},
        {"ampacity": 130, "awg": 2},
        {"ampacity": 150, "awg": 1},
        {"ampacity": 170, "awg": "1/0"},
        {"ampacity": 195, "awg": "2/0"},
        {"ampacity": 225, "awg": "3/0"}
    ]
    # Ensure table is sorted by ampacity 
    cable_table = sorted(cable_table, key=lambda c: int(c["ampacity"]))
    try:
        mca = calculate_mca(load, ambient)
        selected_cable = next((c for c in cable_table if int(c["ampacity"]) >= mca), None)
        if selected_cable:
            components['Cable'] = f"{selected_cable['awg']} AWG ({selected_cable['ampacity']}A)"
    except Exception:
        components['Cable'] = 'N/A'
    # Contactor selection
    try:
        contactor_table = [12, 16, 30, 38, 52, 65, 80, 96]
        min_contactor_amp = 1.1 * load
        selected_contactor = next((amp for amp in contactor_table if amp >= min_contactor_amp), None)
        if selected_contactor:
            components['Contactor'] = f"{selected_contactor}A"
    except Exception:
        components['Contactor'] = 'N/A'
    # Circuit breaker selection
    try:
        cb_table = [6, 10, 16, 20, 25, 32, 40, 50, 63, 70, 90, 125, 150, 200]
        min_cb_amp = 1.75 * load
        max_cb_amp = 2.25 * load
        selected_cb = [amp for amp in cb_table if min_cb_amp < amp < max_cb_amp]
        if selected_cb:
            components['Circuit Breaker'] = ', '.join(str(a) + 'A' for a in selected_cb)
    except Exception:
        components['Circuit Breaker'] = 'N/A'
    # VFD selection
    try:
        vfd_amps = [5.7, 9.5, 12.7, 18, 26, 33, 46, 62, 88]
        vfd_powers = [2.2, 4, 5.5, 7.5, 11, 15, 22, 30, 45]  # kW
        if ambient < 40:
            vfd_amp = 1.25 * load
        else:
            vfd_amp = 1.25 * load / 0.82
        selected_vfd = None
        selected_power = None
        for idx, amp in enumerate(vfd_amps):
            if amp >= vfd_amp:
                selected_vfd = amp
                selected_power = vfd_powers[idx]
                break
        if selected_vfd:
            components['VFD'] = f"{selected_vfd}A, {selected_power}kW"
    except Exception:
        components['VFD'] = 'N/A'
    # Manual Motor Starter selection (MMS)
    try:
        mms_table = [6.3, 10, 16, 25, 32, 40, 50, 63]
        selected_mms = next((m for m in mms_table if m >= load), None)
        if selected_mms:
            components['MMS'] = f"{selected_mms}A"
    except Exception:
        components['MMS'] = 'N/A'
    return components


@app.route('/cable-selection')
def cable_selection():
    compressors = session.get('compressors', [])
    selected_index = session.get('selected_index')
    if selected_index is None or not (0 <= selected_index < len(compressors)):
        flash('Please select a compressor/motor from the main page first.')
        return redirect(url_for('home'))
    selected_compressor = compressors[selected_index]
    load_current = selected_compressor['load']
    ambient_temp = selected_compressor['ambient']
    mca = None
    selected_cable = None
    cable_table = [
        {"ampacity": 14, "awg": 18},
        {"ampacity": 25, "awg": 14},
        {"ampacity": 30, "awg": 12},
        {"ampacity": 40, "awg": 10},
        {"ampacity": 55, "awg": 8},
        {"ampacity": 75, "awg": 6},
        {"ampacity": 95, "awg": 4},
        {"ampacity": 110, "awg": 3},
        {"ampacity": 130, "awg": 2},
        {"ampacity": 150, "awg": 1},
        {"ampacity": 170, "awg": "1/0"},
        {"ampacity": 195, "awg": "2/0"},
        {"ampacity": 225, "awg": "3/0"}
    ]
    cable_table = sorted(cable_table, key=lambda c: int(c["ampacity"]))
    try:
        mca = calculate_mca(load_current, ambient_temp)
        selected_cable = next((c for c in cable_table if int(c["ampacity"]) >= mca), None)
    except Exception:
        mca = 'Invalid input.'
    return render_template('cable_selection.html',
                           compressors=compressors,
                           mca=mca,
                           selected_cable=selected_cable,
                           cable_table=cable_table,
                           load_current=load_current,
                           ambient_temp=ambient_temp,
                           selected_compressor=selected_compressor)


@app.route('/contactor-selection')
def contactor_selection():
    compressors = session.get('compressors', [])
    selected_index = session.get('selected_index')
    if selected_index is None or not (0 <= selected_index < len(compressors)):
        flash('Please select a compressor/motor from the main page first.')
        return redirect(url_for('home'))
    selected = compressors[selected_index]
    min_contactor_amp = None
    selected_contactor = None
    contactor_table = [12, 16, 30, 38, 52, 65, 80, 96]
    load_current = selected['load']
    try:
        min_contactor_amp = 1.1 * load_current
        for amp in contactor_table:
            if amp >= min_contactor_amp:
                selected_contactor = amp
                break
    except Exception:
        min_contactor_amp = 'Invalid input.'
    return render_template('contactor_selection.html', min_contactor_amp=min_contactor_amp, selected_contactor=selected_contactor, contactor_table=contactor_table, load_current=load_current, selected_compressor=selected)

import itertools

@app.route('/circuit-breaker-selection')
def circuit_breaker_selection():
    compressors = session.get('compressors', [])
    selected_index = session.get('selected_index')
    if selected_index is None or not (0 <= selected_index < len(compressors)):
        flash('Please select a compressor/motor from the main page first.')
        return redirect(url_for('home'))
    selected = compressors[selected_index]
    min_cb_amp = None
    max_cb_amp = None
    selected_cb = None
    cb_table_mcb = [6, 10, 16, 20, 25, 32, 40, 50, 63]
    cb_table_mccb = [70, 90, 125, 150, 200]
    cb_table = cb_table_mcb + cb_table_mccb
    cb_table.sort()
    cb_table_zipped = list(itertools.zip_longest(cb_table_mcb, cb_table_mccb, fillvalue=''))
    load_current = selected['load']
    try:
        min_cb_amp = 1.75 * load_current
        max_cb_amp = 2.25 * load_current
        selected_cb = [amp for amp in cb_table if min_cb_amp < amp < max_cb_amp]
    except Exception:
        min_cb_amp = max_cb_amp = 'Invalid input.'
    return render_template('circuit_breaker_selection.html', min_cb_amp=min_cb_amp, max_cb_amp=max_cb_amp, selected_cb=selected_cb, cb_table_mcb=cb_table_mcb, cb_table_mccb=cb_table_mccb, cb_table_zipped=cb_table_zipped, load_current=load_current, selected_compressor=selected)

@app.route('/vfd-selection')
def vfd_selection():
    vfd_amp = None
    selected_vfd = None
    selected_power = None
    vfd_amps = [5.7, 9.5, 12.7, 18, 26, 33, 46, 62, 88]
    vfd_powers = [2.2, 4, 5.5, 7.5, 11, 15, 22, 30, 45]  # kW
    compressors = session.get('compressors', [])
    selected_index = session.get('selected_index')
    if selected_index is None or not (0 <= selected_index < len(compressors)):
        flash('Please select a compressor/motor from the main page first.')
        return redirect(url_for('home'))
    selected = compressors[selected_index]
    load_current = selected['load']
    ambient_temp = selected['ambient']
    try:
        if ambient_temp < 40:
            vfd_amp = 1.25 * load_current
        else:
            vfd_amp = 1.25 * load_current / 0.82
        for idx, amp in enumerate(vfd_amps):
            if amp >= vfd_amp:
                selected_vfd = amp
                selected_power = vfd_powers[idx]
                break
    except Exception:
        vfd_amp = 'Invalid input.'
    vfd_table = list(zip(vfd_amps, vfd_powers))
    return render_template('vfd_selection.html', vfd_amp=vfd_amp, selected_vfd=selected_vfd, selected_power=selected_power, vfd_table=vfd_table, load_current=load_current, ambient_temp=ambient_temp, selected_compressor=selected)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    inventory = read_inventory()
    message = ""
    search_results = None
    wire_types = sorted(set(data['type'] for data in inventory.values()))
    lengths = list(range(2, 21))

    if request.method == 'POST':
        wire_type = request.form.get('wire_type')
        length = request.form.get('length')
        action = request.form.get('action')

        if action == 'search':
            if wire_type:
                search_results = {ref: data for ref, data in inventory.items() if data['type'] == wire_type}
                if not search_results:
                    message = f"No lengths available for {wire_type}."
            else:
                message = "Please select a wire type to search."
        elif action == 'add':
            if wire_type and length:
                ref = generate_reference(wire_type, int(length))
                if ref in inventory:
                    inventory[ref]['quantity'] += 1
                else:
                    inventory[ref] = {
                        'type': wire_type,
                        'length': int(length),
                        'quantity': 1,
                        'reference': ref
                    }
                write_inventory(inventory)
                message = f"Added {wire_type} ({length}m) to inventory."
            else:
                message = "Please select wire type and length to add."
        elif action == 'remove':
            if wire_type and length:
                ref = generate_reference(wire_type, int(length))
                if ref in inventory and inventory[ref]['quantity'] > 0:
                    inventory[ref]['quantity'] -= 1
                    if inventory[ref]['quantity'] == 0:
                        del inventory[ref]
                    write_inventory(inventory)
                    message = f"Removed one {wire_type} ({length}m) from inventory."
                else:
                    message = f"No {wire_type} ({length}m) found in inventory."
            else:
                message = "Please select wire type and length to remove."
    return render_template('index.html', inventory=inventory, message=message, search_results=search_results, wire_types=wire_types, lengths=lengths)

@app.route('/mms-selection')
def mms_selection():
    compressors = session.get('compressors', [])
    selected_index = session.get('selected_index')
    if selected_index is None or not (0 <= selected_index < len(compressors)):
        flash('Please select a compressor/motor from the main page first.')
        return redirect(url_for('home'))
    selected = compressors[selected_index]
    mms_ampacity = None
    selected_mms = None
    mms_ranges = [
        (0.4, 0.63), (0.63, 1), (1, 1.6), (1.6, 2.5), (2.5, 4), (4, 6.3), (6.3, 10),
        (10, 16), (16, 20), (20, 25), (25, 30), (30, 42), (42, 54)
    ]
    load_current = selected['load']
    ambient_temp = selected['ambient']
    try:
        temp_constant = 1.2 if ambient_temp >= 40 else 1
        mms_ampacity = load_current * temp_constant
        for r in mms_ranges:
            if r[0] <= mms_ampacity <= r[1]:
                selected_mms = r
                break
            elif mms_ampacity < mms_ranges[0][0]:
                selected_mms = mms_ranges[0]
                break
    except Exception:
        mms_ampacity = 'Invalid input.'
    return render_template('mms_selection.html', mms_ampacity=mms_ampacity, selected_mms=selected_mms, mms_ranges=mms_ranges, load_current=load_current, ambient_temp=ambient_temp, selected_compressor=selected)


import csv
from io import StringIO
from flask import Response

@app.route('/download-csv')
def download_csv():
    compressors = session.get('compressors', [])
    component_types = ["Cable", "Contactor", "Circuit Breaker", "VFD", "MMS"]
    output = StringIO()
    writer = csv.writer(output)
    header = ["Compressor Name", "Load (A)", "Ambient (°C)"] + component_types
    writer.writerow(header)
    for c in compressors:
        row = [c.get('name', ''), c.get('load', ''), c.get('ambient', '')]
        comps = c.get('components', {})
        for comp_type in component_types:
            row.append(comps.get(comp_type, ''))
        writer.writerow(row)
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=compressor_component_selection.csv"})

    mca = None
    if load_current is not None and ambient_temp is not None:
        try:
            mca = calculate_mca(load_current, ambient_temp)
            for cable in cable_table:
                if cable["ampacity"] >= mca:
                    selected_cable = cable
                    break
        except Exception:
            pass
    # Contactor
    contactor_table = [12, 16, 30, 38, 52, 65, 80, 96]
    selected_contactor = None
    if load_current is not None:
        try:
            min_contactor_amp = 1.1 * load_current
            for amp in contactor_table:
                if amp >= min_contactor_amp:
                    selected_contactor = amp
                    break
        except Exception:
            pass
    # Circuit Breaker
    import itertools
    cb_table_mcb = [6, 10, 16, 20, 25, 32, 40, 50, 63]
    cb_table_mccb = [70, 90, 125, 150, 200]
    cb_table = cb_table_mcb + cb_table_mccb
    cb_table.sort()
    selected_cb = []
    min_cb_amp = max_cb_amp = None
    if load_current is not None:
        try:
            min_cb_amp = 1.75 * load_current
            max_cb_amp = 2.25 * load_current
            selected_cb = [amp for amp in cb_table if min_cb_amp < amp < max_cb_amp]
        except Exception:
            pass
    # VFD
    vfd_amps = [5.7, 9.5, 12.7, 18, 26, 33, 46, 62, 88]
    vfd_powers = [2.2, 4, 5.5, 7.5, 11, 15, 22, 30, 45]  # kW
    selected_vfd = None
    selected_power = None
    vfd_amp = None
    if load_current is not None and ambient_temp is not None:
        try:
            if ambient_temp < 40:
                vfd_amp = 1.25 * load_current
            else:
                vfd_amp = 1.25 * load_current / 0.82
            for idx, amp in enumerate(vfd_amps):
                if amp >= vfd_amp:
                    selected_vfd = amp
                    selected_power = vfd_powers[idx]
                    break
        except Exception:
            pass
    # MMS
    mms_ranges = [
        (0.4, 0.63), (0.63, 1), (1, 1.6), (1.6, 2.5), (2.5, 4), (4, 6.3), (6.3, 10),
        (10, 16), (16, 20), (20, 25), (25, 30), (30, 42), (42, 54)
    ]
    selected_mms = None
    mms_ampacity = None
    if load_current is not None and ambient_temp is not None:
        try:
            temp_constant = 1.2 if ambient_temp >= 40 else 1
            mms_ampacity = load_current * temp_constant
            for r in mms_ranges:
                if r[0] <= mms_ampacity <= r[1]:
                    selected_mms = r
                    break
                elif mms_ampacity < mms_ranges[0][0]:
                    selected_mms = mms_ranges[0]
                    break
        except Exception:
            pass
    # Generate CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Parameter", "Value"])
    writer.writerow(["Load Current (A)", load_current if load_current is not None else ""])
    writer.writerow(["Ambient Temperature (°C)", ambient_temp if ambient_temp is not None else ""])
    writer.writerow(["Cable (AWG)", selected_cable["awg"] if selected_cable else ""])
    writer.writerow(["Cable Ampacity (A)", selected_cable["ampacity"] if selected_cable else ""])
    writer.writerow(["Contactor (A)", selected_contactor if selected_contactor else ""])
    writer.writerow(["Circuit Breaker(s) (A)", ", ".join(str(cb) for cb in selected_cb) if selected_cb else ""])
    writer.writerow(["VFD Current (A)", selected_vfd if selected_vfd else ""])
    writer.writerow(["VFD Power (kW)", selected_power if selected_power else ""])
    writer.writerow(["MMS Range (A)", f"{selected_mms[0]} - {selected_mms[1]}" if selected_mms else ""])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=component_selection.csv"}
    )

if __name__ == "__main__":
    app.run(debug=True)




