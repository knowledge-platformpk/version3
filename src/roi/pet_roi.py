import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt
try:
    def get_pet_image_roi(json_data, from_date, to_date):
        roi = ee.FeatureCollection(json_data)

        # Convert dates to ee.Date objects
        start_date = ee.Date(from_date)
        end_date = ee.Date(to_date)

        def scale_index(img):
            return img.multiply(0.1).copyProperties(img,['system:time_start','date','system:time_end'])
        # Filter the ERA temperature collection by date
        pet_collection = ee.ImageCollection("MODIS/061/MOD16A2").filterBounds(roi).filterDate(start_date, end_date).select('PET').map(scale_index)

        # Calculate the mean temperature image
        mean_pet_image = pet_collection.mean().clip(roi)

        minMax = mean_pet_image.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=roi,
            scale=30,
            bestEffort=True
        )

        area = roi.geometry(0.01).area().divide(1e6)

        try:
        # Access min and max values from the minMax dictionary
            min_image = minMax.get('PET_min')
            max_image = minMax.get('PET_max')

            st.session_state['min'] = min_image.getInfo()
            st.session_state['max'] = max_image.getInfo()
            st.session_state['area'] = area.getInfo()
        except:
            st.session_state['min'] = 0
            st.session_state['max'] = 75
            st.session_state['area'] = area.getInfo()

        return mean_pet_image
    def create_pet_timeseries_roi(json_data, from_date, to_date):
        roi = ee.FeatureCollection(json_data)

        # Convert dates to ee.Date objects
        start_date = ee.Date(from_date)
        end_date = ee.Date(to_date)
        def scale_index(img):
            return img.multiply(0.1).copyProperties(img,['system:time_start','date','system:time_end'])
        # Filter the ERA temperature collection by date
        pet_collection = ee.ImageCollection("MODIS/061/MOD16A2").filterBounds(roi).filterDate(start_date, end_date).select('PET').map(scale_index)

        # Create a list of dates and mean temperature values
        timeseries = pet_collection.map(lambda image: ee.Feature(None, {
            'date': image.date().format(),
            'PET': image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=1000  # Adjust scale according to your data resolution
            ).get('PET')
        }))

        # Convert to a Pandas DataFrame
        timeseries_list = timeseries.reduceColumns(ee.Reducer.toList(2), ['date', 'PET']).values().get(0).getInfo()
        df = pd.DataFrame(timeseries_list, columns=['date', 'PET'])
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        st.session_state['pet_chart_data'] = df

        # Create a time-series plot
        fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
        df.plot(x='date', y='PET', ax=ax, legend=True, title='PET Time Series')
        plt.xlabel('Date', fontsize=6)
        plt.ylabel('Potential Evapotranspiration (PET) - kg/m^2/8day')
        plt.grid(True)
        plt.tight_layout()

        return fig
except Exception as e:
        st.write('No Data Available')