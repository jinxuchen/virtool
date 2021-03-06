import { max } from "lodash-es";
import { scaleLinear } from "d3-scale";
import { select } from "d3-selection";
import { area } from "d3-shape";
import PropTypes from "prop-types";
import React from "react";
import { Flex } from "../../../base";

const createChart = (element, data, width) => {
    let svg = select(element).append("svg");

    const margin = {
        top: 10,
        left: 15,
        bottom: 10,
        right: 15
    };

    const yMax = max(data);

    svg.append("text")
        .text(yMax.toString())
        .remove();

    svg.remove();

    const length = data.length;

    const height = 60 - margin.top - margin.bottom;

    width -= 30;

    const x = scaleLinear()
        .range([0, width])
        .domain([0, length]);

    const y = scaleLinear()
        .range([height, 0])
        .domain([0, yMax]);

    // Construct the SVG canvas.
    svg = select(element)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    if (data) {
        const areaDrawer = area()
            .x((d, i) => x(i))
            .y0(d => y(d))
            .y1(height);

        svg.append("path")
            .datum(data)
            .attr("class", "depth-area")
            .attr("d", areaDrawer);
    }
};

export default class OTUCoverage extends React.Component {
    static propTypes = {
        id: PropTypes.string,
        filled: PropTypes.array
    };

    componentDidMount() {
        window.addEventListener("resize", this.renderChart);
        this.renderChart();
    }

    shouldComponentUpdate(nextProps) {
        return this.props.id !== nextProps.id;
    }

    componentDidUpdate() {
        this.renderChart();
    }

    componentWillUnmount() {
        window.removeEventListener("resize", this.renderChart);
    }

    renderChart = () => {
        while (this.chartNode.firstChild) {
            this.chartNode.removeChild(this.chartNode.firstChild);
        }

        createChart(this.chartNode, this.props.filled, this.chartNode.scrollWidth);
    };

    render() {
        return (
            <Flex>
                <div style={{ display: "flex", flex: "1 0 auto" }} ref={node => (this.chartNode = node)} />
            </Flex>
        );
    }
}
