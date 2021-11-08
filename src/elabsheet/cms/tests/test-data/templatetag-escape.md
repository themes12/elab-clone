Source with template tags
========================

The following tags must be rendered with no error.

{% load static %}{% load elab_conf %}

{% static 'js/script.js' %}

{% static 'img/icon.png' %}

{% site_name %}something in between{% site_name %}

Some template tag wrapped inside an HTML tag like <span style="color:red">{% site_name %}</span>

Part of a header {% site_name %}
================================
