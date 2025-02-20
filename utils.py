import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go


class SankeyPlot(object):
    """
    Class for creating and visualizing Sankey diagrams using Plotly.

    Attributes:
        data (pd.DataFrame): Input data for generating the Sankey diagram.
        target_list (list): List of column names specifying the flow sequence.

    Methods:
        create_sankey_table(): Generates a DataFrame for Sankey diagram links.
        get_colors_list(): Returns a list of colors for nodes and links.
        plot_sankey(save_path=None, show_numbers=False, title=None):
            Plots the Sankey diagram and optionally saves it to a file.
    """
    def __init__(self, data, target_list):
        self.data = data
        self.target_list = target_list

        self.df_sankey = self.create_sankey_table()

        target_value = self.df_sankey.groupby("target").sum()["value"].reset_index().rename({"target": "source_target"},
                                                                                            axis=1)
        source_value = self.df_sankey.groupby("source").sum()["value"].reset_index().rename({"source": "source_target"},
                                                                                            axis=1)
        self.nodes_count = pd.concat([target_value, source_value]).drop_duplicates()

        # Create Sankey table with Plotly setting
        self.df_sankey_plotly = self.create_sankey_table()
        self.unique_source_target = list(pd.unique(self.df_sankey[['source', 'target']].values.ravel('K')))
        self.mapping_dict = {k: v for v, k in enumerate(self.unique_source_target)}
        self.df_sankey_plotly['source'] = self.df_sankey_plotly['source'].map(self.mapping_dict)
        self.df_sankey_plotly['target'] = self.df_sankey_plotly['target'].map(self.mapping_dict)
        self.links_dict = self.df_sankey_plotly.to_dict(orient='list')

        self.colors = self.get_colors_list()
        self.df_label_color = pd.DataFrame([self.unique_source_target, self.colors],
                                           index=["label", "color"]).transpose()
        self.df_label_color["label"] = self.df_label_color["label"].map(self.mapping_dict)
        self.df_sankey_plotly = self.df_sankey_plotly.merge(self.df_label_color, left_on="source", right_on="label",
                                                            how="left")

    def create_sankey_table(self):
        df_sankey = pd.DataFrame(columns=["source", "target", "value"])
        for i in range(len(self.target_list) - 1):
            source_name = self.target_list[i]
            for source_item in self.data[self.target_list[i]].unique():
                target_name = self.target_list[i + 1]
                df_temp = self.data[self.data[source_name] == source_item].groupby(target_name).count()[
                    "Submission Number"]
                df_temp = df_temp.reset_index()
                df_temp["source"] = source_item
                df_temp = df_temp.rename({"Submission Number": "value", target_name: "target"}, axis=1)
                df_sankey = pd.concat([df_sankey, df_temp])
        df_sankey = df_sankey.reset_index(drop=True)
        return df_sankey.drop(df_sankey[df_sankey["value"] == 0].index, axis=0)

    def get_colors_list(self):
        colors_list = list(plt.cm.tab20.colors) + list(plt.cm.Dark2.colors) + list(plt.cm.Pastel1.colors) + list(
            plt.cm.tab20.colors)
        colors = [f"rgba({int(color[0] * 255)}, {int(color[1] * 255)}, {int(color[2] * 255)}, 0.7)" for color in
                  colors_list]
        return colors[:len(self.unique_source_target)]

    def plot_sankey(self, save_path=None, show_numbers=False, title=None):
        if show_numbers:
            node_labels = [
                f"{name.replace('_a', '').replace('_b', '')} ({self.nodes_count[self.nodes_count['source_target'] == name]['value'].values[0]})"
                for name in self.unique_source_target]
        else:
            node_labels = [f"{name.replace('_a', '').replace('_b', '')}" for name in self.unique_source_target]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=self.df_label_color["color"].values
            ),
            link=dict(
                source=self.links_dict["source"],
                target=self.links_dict["target"],
                value=self.links_dict["value"],
                color=self.df_sankey_plotly["color"].values
            ))])

        fig.update_layout(font_size=16, width=1000, height=600, title=title)

        if save_path:
            fig.write_image(save_path, scale=3, format=os.path.splitext(save_path)[1].replace(".", ""))

        return fig
