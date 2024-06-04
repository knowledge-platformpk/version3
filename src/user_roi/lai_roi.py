import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt


def get_LAI_image_roi(json_data, from_date, to_date):
    json_data = Map.user_roi
    roi = ee.Geometry(json_data)
    # Convert dates to ee.Date objects
    start_date = ee.Date(from_date)
    end_date = ee.Date(to_date)

    def scale_index(img):
        return img.multiply(0.1).copyProperties(img,['system:time_start','date','system:time_end'])
    # Filter the ERA temperature collection by date
    LAI_collection = ee.ImageCollection("MODIS/061/MOD15A2H").filterDate(start_date, end_date).select('Lai_500m').map(scale_index)

    # Calculate the mean temperature image
    mean_LAI_image = LAI_collection.mean().clip(roi)

    minMax = mean_LAI_image.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=roi,
        scale=30,
        bestEffort=True
    )

    try:
        # Access min and max values from the minMax dictionary
        min_image = minMax.get('Lai_500m_min')
        max_image = minMax.get('Lai_500m_max')

        st.session_state['min'] = min_image.getInfo()
        st.session_state['max'] = max_image.getInfo()
    except:
        st.session_state['min'] = -1
        st.session_state['max'] = 1

    return mean_LAI_image
def create_LAI_timeseries_roi(json_data, from_date, to_date):
    roi = ee.FeatureCollection(json_data)

    # Convert dates to ee.Date objects
    start_date = ee.Date(from_date)
    end_date = ee.Date(to_date)
    def scale_index(img):
        return img.multiply(0.1).copyProperties(img,['system:time_start','date','system:time_end'])
    # Filter the ERA temperature collection by date
    LAI_collection = ee.ImageCollection("MODIS/061/MOD15A2H").filterBounds(roi).filterDate(start_date, end_date).select('Lai_500m').map(scale_index)

    # Create a list of dates and mean temperature values
    timeseries = LAI_collection.map(lambda image: ee.Feature(None, {
        'date': image.date().format(),
        'Lai_500m': image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=500  # Adjust scale according to your data resolution
        ).get('Lai_500m')
    }))

    # Convert to a Pandas DataFrame
    timeseries_list = timeseries.reduceColumns(ee.Reducer.toList(2), ['date', 'Lai_500m']).values().get(0).getInfo()
    df = pd.DataFrame(timeseries_list, columns=['date', 'Lai_500m'])
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%b %Y')
    st.session_state['LAI_chart_data'] = df

    # Create a time-series plot
    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
    df.plot(x='date', y='Lai_500m', ax=ax, legend=True, title='LAI Time Series')
    plt.xlabel('Date', fontsize=6)
    plt.ylabel('Leaf Area Index (LAI)')
    plt.grid(True)
    plt.tight_layout()

    return fig
